import os
import threading
from contextlib import contextmanager
from typing import List, Sequence, Union

import numpy as np
from paddleocr import TextRecognition
import log
from filetools import ftools

try:
    import onnxruntime as ort

    _AVAILABLE_PROVIDERS = set(ort.get_available_providers())
except Exception:
    _AVAILABLE_PROVIDERS = set()

ImageInput = Union[str, os.PathLike, np.ndarray]


@contextmanager
def _silence_native_stderr():
    """Глушит stderr на уровне файлового дескриптора (работает и для C++ кода)."""
    saved_fd = os.dup(2)
    null_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(null_fd, 2)
        yield
    finally:
        os.dup2(saved_fd, 2)
        os.close(saved_fd)
        os.close(null_fd)


def _resolve_device(prefer_gpu: bool) -> str:
    """Выбирает устройство: GPU только если он реально доступен, иначе CPU."""
    if prefer_gpu and "CUDAExecutionProvider" in _AVAILABLE_PROVIDERS:
        return "gpu:0"
    return "cpu"


def _extract_text(item) -> str:
    """Достаёт распознанный текст из результата в любом из поддерживаемых форматов."""
    if item is None:
        return ""
    if isinstance(item, dict):
        return str(item.get("rec_text") or "")
    try:  # объекты результатов PaddleOCR 3.x поддерживают индексацию
        return str(item["rec_text"] or "")
    except Exception:
        pass
    if isinstance(item, (list, tuple)) and item:  # legacy-формат: [[text, score]]
        first = item[0]
        if isinstance(first, (list, tuple)) and first:
            return str(first[0])
    return ""


class CyrillicOCR:
    # Кэш загруженных моделей: одна модель на (папка, устройство) на всё приложение
    _model_cache: dict = {}
    _cache_lock = threading.Lock()

    def __init__(self, model_dir: str = "./model", device: str = "auto",
                 batch_size: int = 8):
        self.log = log.logger("app-OCR", ftools().get_logger_path())
        self.batch_size = max(1, batch_size)
        # УДАЛЕНО: self._predict_lock = threading.Lock()
        # (ONNX Runtime потокобезопасен для инференса, лок только сериализует вызовы)

        if not os.path.exists(os.path.join(model_dir, "inference.onnx")):
            self.log.info(f"Модель не найдена в {model_dir}")
            raise FileNotFoundError(f"Модель не найдена в {model_dir}")

        prefer_gpu = device in ("auto", "gpu")
        target = _resolve_device(prefer_gpu)
        self.model, self.device = self._get_or_load(model_dir, target)
        self.log.info(f"OCR готов, устройство: {self.device}")

    # ------------------------------------------------------------------ загрузка

    def _get_or_load(self, model_dir: str, target: str):
        key = (os.path.abspath(model_dir), target)
        with self._cache_lock:
            if key in self._model_cache:
                self.log.info("Модель взята из кэша.")
                return self._model_cache[key]

            model, used = self._load(model_dir, target)
            self._model_cache[(key[0], used)] = (model, used)
            return model, used

    def _load(self, model_dir: str, target: str):
        self.log.info(f"Загрузка модели из {model_dir} на устройстве {target}...")
        try:
            model = self._create_model(model_dir, target)
            used = target
        except Exception as e:
            if target == "cpu":
                raise
            self.log.info(f"Не удалось загрузить на {target} ({e}). Переключаюсь на CPU.")
            model = self._create_model(model_dir, "cpu")
            used = "cpu"

        self._warmup(model)
        return model, used

    def _create_model(self, model_dir: str, device: str) -> TextRecognition:
        # Подавление stderr оставлено ТОЛЬКО при инициализации, где возможны C++ предупреждения
        with _silence_native_stderr():
            return TextRecognition(
                model_name="PP-OCRv6_medium_rec",
                model_dir=model_dir,
                engine="onnxruntime",
                device=device,
            )

    def _warmup(self, model: TextRecognition) -> None:
        """Прогрев: создаёт сессию и аллокации заранее, на синтетическом изображении."""
        dummy = np.full((48, 320, 3), 255, dtype=np.uint8)
        with _silence_native_stderr():
            try:
                model.predict(dummy)
            except Exception as e:
                self.log.info(f"Прогрев не удался (не критично): {e}")

    # ------------------------------------------------------------- распознавание

    def _check_input(self, image: ImageInput) -> ImageInput:
        if isinstance(image, np.ndarray):
            return image
        path = os.fspath(image)
        if not os.path.exists(path):
            self.log.error(f"Изображение не найдено: {path}")
            raise FileNotFoundError(f"Изображение не найдено: {path}")
        return path

    def predict(self, image: ImageInput) -> str:
        """Распознаёт одно изображение (путь или numpy-массив)."""
        return self.predict_batch([image])[0]

    def predict_batch(self, images: Sequence[ImageInput]) -> List[str]:
        """Распознаёт список изображений пакетами. Возвращает тексты в том же порядке."""
        inputs = [self._check_input(img) for img in images]
        results: List[str] = []

        for start in range(0, len(inputs), self.batch_size):
            chunk = inputs[start:start + self.batch_size]

            # УДАЛЕНЫ: with self._predict_lock, _silence_native_stderr():
            # Прямой вызов максимально быстр и позволяет ONNX Runtime работать эффективно

            raw = self.model.predict(chunk)
            raw = list(raw) if raw is not None else []
            results.extend(_extract_text(r) for r in raw)

        # Защита от рассинхронизации: результатов должно быть ровно столько же, сколько входов
        if len(results) != len(inputs):
            self.log.error(f"Количество результатов ({len(results)}) != входов ({len(inputs)})")
            results = (results + [""] * len(inputs))[:len(inputs)]
        return results
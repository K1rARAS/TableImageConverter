import os
import sys
import ctypes
from paddleocr import TextRecognition
import log
from filetools import ftools


class CyrillicOCR:
    def __init__(self, model_dir: str = "./model", device: str = "cpu"):
        self.log = log.logger('app-OCR',ftools().get_logger_path())
        if not os.path.exists(os.path.join(model_dir, "inference.onnx")):
            self.log.info(f"Модель не найдена в {model_dir}")
            raise FileNotFoundError(f"Модель не найдена в {model_dir}")

        self.log.info(f"Загрузка модели из {model_dir}...")

        # --- ЯДЕРНЫЙ МЕТОД ДЛЯ WINDOWS (через ctypes) ---
        # Сохраняем текущий дескриптор stderr
        original_stderr_fd = os.dup(2)

        # Открываем системный "черный ящик" (NUL)
        null_fd = os.open(os.devnull, os.O_WRONLY)

        try:
            # Заставляем саму ОС перенаправить поток ошибок в NUL
            os.dup2(null_fd, 2)

            # Загружаем модель (весь мусор от C++ бесследно исчезает)
            self.model = TextRecognition(
                model_name="PP-OCRv6_medium_rec",
                model_dir=model_dir,
                engine="onnxruntime",
                device=device
            )

            # Делаем холостой прогон, чтобы модель создала сессию именно сейчас,
            # пока вывод отключен. Если картинки нет, просто пропускаем.
            # self.model.predict("dummy.jpg")  # (раскомментируйте, если спам лезет при predict)

        finally:
            # Восстанавливаем стандартный вывод ошибок
            os.dup2(original_stderr_fd, 2)
            os.close(original_stderr_fd)
            os.close(null_fd)
        # -----------------------------------------------

        self.log.info("Модель успешно загружена.")

    def predict(self, image_path: str) -> str:
        if not os.path.exists(image_path):
            self.log.error(f"Изображение не найдено: {image_path}")
            raise FileNotFoundError(f"Изображение не найдено: {image_path}")

        # Если спам всё-таки лезет именно при predict, можно обернуть и его:
        original_stderr_fd = os.dup(2)
        null_fd = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(null_fd, 2)
            result = self.model.predict(image_path)
        finally:
            os.dup2(original_stderr_fd, 2)
            os.close(original_stderr_fd)
            os.close(null_fd)

        if result and len(result) > 0:
            if isinstance(result[0], dict):
                return result[0].get('rec_text', '')
            elif isinstance(result[0], list) and len(result[0]) > 0:
                return result[0][0][0]
        return ""

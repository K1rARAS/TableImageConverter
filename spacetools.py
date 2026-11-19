import os
import re
from collections import defaultdict
from progressbar import progressbar
# --- импорт функций из первого файла (image utils) ---
from imagetools import (
    read_image,
    get_angle,
    rotate_no_crop,
    process_table_with_custom_ocr,)
import cv2

# --- импорт OCR из второго файла ---
from OCRmodel import CyrillicOCR

# --- ваши утилиты ---
import log
from filetools import ftools


class ImageTools:
    """
    Пайплайн: изображение -> выравнивание -> нарезка ячеек -> OCR -> text/text/.../text
    Использует:
      - read_image / get_angle / rotate_no_crop / process_table_with_custom_ocr  (image_utils)
      - CyrillicOCR                                                             (ocr_cyrillic)
    """

    def __init__(self, ft_instance=None, ocr_instance=None):
        self.ft = ft_instance if ft_instance is not None else ftools()
        self.ocr = ocr_instance if ocr_instance is not None else CyrillicOCR(self.ft.model)
        self.log = log.logger("app-imtools", self.ft.get_logger_path())

        self.obj_plt = None   # путь к выровненному изображению
        self.buffer = None    # путь к буферу с ячейками
        self.cnt = None       # количество ячеек
        self.result = None    # итоговый text/text/.../text

    # ------------------------------------------------------------------ #
    # шаг 1: выравнивание
    # ------------------------------------------------------------------ #
    def spectrate(self, path: str) -> str:
        """Выравнивает изображение и сохраняет рядом (*_aligned.png)."""
        angle = get_angle(path)
        if angle is not None and abs(angle) > 0.1:
            rotated = rotate_no_crop(path, angle)
            out_path = self.ft.get_sub_out(path, "_aligned")

            # запись с поддержкой кириллицы в пути
            ok, buf = cv2.imencode(".png", rotated)
            if ok:
                buf.tofile(out_path)
                return out_path
            self.log.error(f"Не удалось сохранить выровненное изображение: {out_path}")
        return path

    # ------------------------------------------------------------------ #
    # шаг 2: нарезка ячеек (делегируем в process_table_with_custom_ocr)
    # ------------------------------------------------------------------ #
    def divide(self, image_path: str | None = None, output_dir="cells", progress_callback=None) -> dict:
        """
        Нарезает ячейки и прогоняет OCR через process_table_with_custom_ocr.
        Возвращает dict: {(table_idx, row_idx, col_idx): {"text", "bbox", "file"}}.
        """
        target = image_path or self.obj_plt
        if target is None:
            raise ValueError("Не задан путь к изображению для нарезки")

        # Создаем фабрику прогресса
        from progressbar import progressbar as _pb
        factory = None
        if progress_callback is not None:
            factory = lambda name, max_, w: _pb(name, max_, w, callback=progress_callback)

        results = process_table_with_custom_ocr(
            image_path=str(target),
            ocr_instance=self.ocr,
            output_dir=output_dir,         # передаем аргумент
            keep_files=False,
            min_cell_size=4,
            progress_factory=factory       # передаем фабрику в OCR
        )

        self.cnt = len(results)
        self.buffer = output_dir

        if not results:
            self.log.info("Таблицы не найдены или ячейки пусты")
        return results

    # ------------------------------------------------------------------ #
    # шаг 3: сборка text/text/.../text
    # ------------------------------------------------------------------ #
    def build_text(self, results: dict, delimiter: str = "/") -> str:
        """Собирает результаты OCR в строку вида 'a/b/c\\nd/e/f'."""
        if not results:
            return ""
        grid = defaultdict(dict)
        max_row = max_col = -1

        for (t, r, c), item in results.items():
            grid[r][c] = item.get("text", "")
            max_row = max(max_row, r)
            max_col = max(max_col, c)

        if max_row < 0:
            return ""

        lines = []
        for r in range(max_row + 1):
            cells = [grid[r].get(c, "") for c in range(max_col + 1)]
            lines.append(delimiter.join(cells))
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # публичные методы пайплайна
    # ------------------------------------------------------------------ #
    def download(self, path: str) -> None:
        """Выравнивает таблицу и подготавливает путь."""
        self.obj_plt = self.spectrate(str(path)) or str(path)

    def pred(self) -> str:
        """Прогоняет OCR и собирает итоговую таблицу."""
        results = self.divide(self.obj_plt)
        self.result = self.build_text(results)
        return self.result

    def start(self, path, output_dir="cells", progress_callback=None):
        """Главный метод: загрузка -> нарезка -> распознавание."""

        # 1. Выравниваем изображение
        self.download(path)

        # 2. Нарезаем и распознаем (передаем callback и output_dir!)
        results = self.divide(self.obj_plt, output_dir=output_dir, progress_callback=progress_callback)

        # 3. Собираем текст
        self.result = self.build_text(results)
        return self.result

    def getresult(self) -> str | None:
        return self.result


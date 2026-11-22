# Terminal.py
import os, sys
from pathlib import Path
from threading import Thread
from time import sleep

from filetools import ftools
from log import logger
from spacetools import ImageTools
from convtools import xlsx_convert


class Terminal:
    """
    Ядро приложения: держит ftools + ImageTools.
    Методы-действия вызываются из GUI.
    Никаких input()/msvcrt — только бизнес-логика.
    """
    def __init__(self):
        self.ft = ftools()
        self.log = logger('app-Terminal', self.ft.get_logger_path())

        # Первичная инициализация каталогов/User.json
        if not self.ft.base.exists() or not self.ft.user.exists():
            self.ft.create()

        # Модель грузим сразу (один раз)
        self.space = ImageTools(self.ft)
        self.output = self.ft.read_j(self.ft.user)["Output"]

    # ---------- действия ----------
    def get_name(self) -> str:
        return self.ft.read_j(self.ft.user).get("Name", "Uknown")

    def set_name(self, name: str):
        self.ft.rename(name)

    def get_output(self) -> str | None:
        out = self.ft.read_j(self.ft.user).get("Output")
        if out and out != "None":
            return out
        return None

    def set_output(self, path: str):
        path = str(path).strip().strip('"').strip("'").strip()
        if not Path(path).exists():
            raise FileNotFoundError(f"Путь не существует: {path}")
        self.ft.rewrite_out(path)
        self.output = path

    def get_history(self) -> list:
        return self.ft.read_j(self.ft.user).get("History", [])

    def clear_history(self):
        self.ft.delete_history()

    def process_image(self, image_path: str, progress_callback=None) -> str:
        """Полный пайплайн: выравнивание -> OCR -> сохранение xlsx + истории."""

        # 1. Получаем путь и сохраняем его в переменную out_dir
        out_dir = self.get_output()
        cell_buffer_dir = str(self.ft.buffer.resolve())

        # 2. Проверяем, что папка выбрана
        if not out_dir:
            raise RuntimeError("Папка сохранений не выбрана (Директории)")

        self.ft.create_out()

        # 3. Передаём эту переменную в space.start()
        self.space.start(
            image_path,
            output_dir=cell_buffer_dir,
            progress_callback=progress_callback
        )

        text = self.space.getresult()

        # ВАЖНО: у вас в Terminal.add_history(text, select) был перепутан порядок
        self.ft.add_history(image_path, text)
        xlsx_convert(text, image_path)
        return text
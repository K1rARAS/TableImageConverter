import os
from PyQt6.QtCore import QObject, pyqtSignal


class ConsoleProgress:
    """Старое поведение — вывод в консоль (оставляем для CLI)."""
    def __init__(self, name: str, maximum: int, w: int):
        if maximum <= 0:
            raise ValueError("maximum must be > 0")
        self.maximum, self.w, self.name, self.count = maximum, w, name, 0

    def progress(self, value: int):
        self.count += value
        percent = int(self.count / self.maximum * 100)
        score = int(self.count / self.maximum * self.w)
        self.clear()
        print(
            f"{self.name}\nВыполнено: {self.count}/{self.maximum}\n"
            f"Прогресс задачи {percent}%: {'/' * score}{'.' * (self.w - score)}",
            flush=True,
        )

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")


class GuiProgress(QObject):
    """
    GUI-вариант: сигнал летит в главный поток, MainWindow обновляет QProgressBar.
    Сигнал из QThread в слот главного потока доставляется через QueuedConnection —
    это потокобезопасно, трогать виджеты из воркера не нужно.
    """
    updated = pyqtSignal(int, int, int, str)  # count, maximum, percent, bar

    def __init__(self, name: str, maximum: int, w: int, parent=None):
        super().__init__(parent)
        if maximum <= 0:
            raise ValueError("maximum must be > 0")
        self.maximum, self.w, self.name, self.count = maximum, w, name, 0

    def progress(self, value: int):
        self.count += value
        percent = int(self.count / self.maximum * 100)
        score = int(self.count / self.maximum * self.w)
        bar = "/" * score + "." * (self.w - score)
        self.updated.emit(self.count, self.maximum, percent, bar)
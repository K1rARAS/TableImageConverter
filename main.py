import sys
import os
from filetools import ftools

# --- БЛОК ПЕРЕХВАТА ОШИБОК (ДОЛЖЕН БЫТЬ САМЫМ ПЕРВЫМ) ---
f = ftools()
if sys.stdout is None or sys.stderr is None:
    # Определяем папку, где лежит exe-файл
    if getattr(sys, 'frozen', False):
        base_dir = str(f.logs)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    log_file = open(os.path.join(base_dir, "error_log.txt"), "w", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = log_file
    if sys.stderr is None:
        sys.stderr = log_file

# --- ТЕПЕРЬ МОЖНО ИМПОРТИРОВАТЬ ОСТАЛЬНОЕ ---
import ctypes
import traceback
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer

# Обернем импорт MainWindow в try-except, чтобы поймать ошибку, если она там
try:
    from MainWindow import MainWindow
except Exception as e:
    traceback.print_exc()
    sys.exit(1)


def _assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "assets"
    return Path(__file__).resolve().parent / "assets"


if __name__ == "__main__":
    try:
        icon_path = _assets_dir() / "app.ico"

        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "TableImageConverter.App.Final.v3"
            )

        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(str(icon_path)))

        win = MainWindow()
        win.show()

        if sys.platform == "win32":
            def force_icon():
                try:
                    hwnd = int(win.winId())
                    hicon_small = ctypes.windll.user32.LoadImageW(0, str(icon_path), 1, 16, 16, 0x10)
                    hicon_big = ctypes.windll.user32.LoadImageW(0, str(icon_path), 1, 32, 32, 0x10)
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon_small)
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon_big)
                except Exception as e:
                    print("❌ Ошибка установки иконки:", e)


            QTimer.singleShot(200, force_icon)

        sys.exit(app.exec())

    except Exception:
        # Если программа упала во время работы, пишем ошибку в файл
        traceback.print_exc()
        sys.exit(1)
# MainWindow.py
import sys, traceback
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QApplication, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QSizeGrip, QFrame, QFileDialog,
    QLineEdit, QListWidget, QMessageBox, QTextEdit, QStackedWidget,QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QRadialGradient, QPainterPath,
    QDragEnterEvent, QDropEvent, QIcon
)

from Terminal import Terminal
from convtools import xlsx_convert


# ----------------------- Воркер для тяжёлого OCR -----------------------
class ProcessWorker(QThread):
    finished_ok      = pyqtSignal(str)
    failed           = pyqtSignal(str)
    cancelled        = pyqtSignal()                 # ← новое
    progress_changed = pyqtSignal(int, str)

    def __init__(self, terminal, image_path):
        super().__init__()
        self.terminal = terminal
        self.image_path = image_path
        self._cancelled = False                     # ← флаг отмены

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            def _cb(percent, text):
                if self._cancelled:                 # ← прерываемся на первом же шаге
                    raise InterruptedError("Операция отменена пользователем")
                self.progress_changed.emit(percent, text)

            text = self.terminal.process_image(
                self.image_path, progress_callback=_cb
            )
            if self._cancelled:
                raise InterruptedError("Операция отменена пользователем")
            self.finished_ok.emit(text)
        except InterruptedError:
            self.cancelled.emit()                   # ← отдельный сигнал
        except Exception as e:
            self.failed.emit(f"{e}\n\n{traceback.format_exc()}")
# ---------------------------- UI ----------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        icon_path = Path(__file__).resolve().parent / "assets" / "app.ico"
        self.setWindowIcon(QIcon(str(icon_path)))
        self.setWindowTitle("Table Image Converter")
        self._drag_pos = None
        self.core = Terminal()          # инициализация ftools + OCR
        self.worker: ProcessWorker | None = None
        self.init_win()
        self.setWindowIcon(QIcon(str(icon_path)))

    # ---------- Отрисовка ----------
    def paintEvent(self, event):
        window = QPainter(self)
        window.setRenderHint(QPainter.RenderHint.Antialiasing)

        dark_blue = QColor('#00002F')
        orange    = QColor('#FF7A00')

        pen = QPen(QColor("#0000FF"), 2, Qt.PenStyle.SolidLine)
        window.setPen(pen)

        gradient = QRadialGradient(
            self.width() / 2, self.height() / 2,
            max(self.width(), self.height()) / 2
        )
        gradient.setColorAt(0.0, orange)
        gradient.setColorAt(1.0, dark_blue)

        path = QPainterPath()
        path.addRoundedRect(1, 1, self.width() - 2, self.height() - 2, 20, 20)

        window.fillPath(path, gradient)
        window.drawPath(path)

    # ---------- Инициализация ----------
    def init_win(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(760, 520)
        self.setAcceptDrops(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.title_bar = self.create_title_bar()
        self.main_layout.addWidget(self.title_bar)

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.main_layout.addWidget(self.content, 1)

        self.build_content()

    def create_title_bar(self):
        bar = QWidget()
        bar.setFixedHeight(40)
        bar.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(15, 0, 5, 0)
        layout.setSpacing(5)

        title = QLabel("Table Image Converter")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")

        btn_min   = QPushButton("—")
        btn_max   = QPushButton("□")
        btn_close = QPushButton("✕")

        for btn in (btn_min, btn_max, btn_close):
            btn.setFixedSize(32, 32)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: white;
                    border: none; font-size: 14px; border-radius: 6px;
                }
                QPushButton:hover { background: rgba(255, 255, 255, 40); }
            """)

        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent; color: white;
                border: none; font-size: 14px; border-radius: 6px;
            }
            QPushButton:hover { background: rgba(255, 60, 60, 180); }
        """)

        btn_min.clicked.connect(self.showMinimized)
        btn_max.clicked.connect(self.toggle_max)
        btn_close.clicked.connect(self.close)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(btn_min)
        layout.addWidget(btn_max)
        layout.addWidget(btn_close)
        return bar

    # ---------- Основной контент ----------
    def build_content(self):
        root = QHBoxLayout(self.content)
        root.setContentsMargins(20, 15, 20, 15)
        root.setSpacing(15)

        # ---- Левая панель: меню ----
        menu = QFrame()
        menu.setFixedWidth(180)
        menu.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 10, 50, 180);
                border: 2px solid #0000ff;
                border-radius: 10px;
            }
        """)
        menu_lay = QVBoxLayout(menu)
        menu_lay.setContentsMargins(10, 10, 10, 10)
        menu_lay.setSpacing(8)

        self.btn_drop_zone = QPushButton("📂  Обработать")
        self.btn_dirs      = QPushButton("🗂  Директории")
        self.btn_history   = QPushButton("🕘  История")
        self.btn_profile   = QPushButton("👤  Профиль")

        for b in (self.btn_drop_zone, self.btn_dirs, self.btn_history, self.btn_profile):
            b.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,15);
                    color: white; border: 1px solid rgba(255,255,255,60);
                    border-radius: 8px; padding: 8px; text-align: left;
                }
                QPushButton:hover { background: rgba(255,122,0,120); }
            """)

        self.btn_drop_zone.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_dirs.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.btn_history.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.btn_profile.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        menu_lay.addWidget(self.btn_drop_zone)
        menu_lay.addWidget(self.btn_dirs)
        menu_lay.addWidget(self.btn_history)
        menu_lay.addWidget(self.btn_profile)
        menu_lay.addStretch()

        # ---- Правая панель: стек страниц ----
        self.stack = QStackedWidget()
        self.stack.addWidget(self.page_process())
        self.stack.addWidget(self.page_directories())
        self.stack.addWidget(self.page_history())
        self.stack.addWidget(self.page_profile())

        root.addWidget(menu)
        root.addWidget(self.stack, 1)

        # QSizeGrip
        grip = QSizeGrip(self)
        root.addWidget(grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

    # ---------- Страница: Обработать ----------
    def page_process(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        # --- drop-зона ---
        self.drop_frame = QFrame()
        self.drop_frame.setAcceptDrops(True)
        self.drop_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 10, 50, 180);
                border: 2px dashed #0000ff;
                border-radius: 10px;
            }
        """)
        drop_lay = QVBoxLayout(self.drop_frame)
        self.drop_hint = QLabel("Перетащите изображение таблицы сюда\nили нажмите кнопку ниже")
        self.drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_hint.setStyleSheet(
            "color:#8080ff; font-size:14px; background:transparent; border:none;"
        )
        drop_lay.addWidget(self.drop_hint)

        # --- кнопки: выбрать файл + отмена ---
        btn_row = QHBoxLayout()

        btn_pick = QPushButton("Выбрать файл…")
        btn_pick.clicked.connect(self.pick_file)

        self.btn_cancel = QPushButton("✖  Отмена")
        self.btn_cancel.setEnabled(False)          # активна только во время обработки
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background: rgba(255, 60, 60, 160); color: white;
                border: 1px solid rgba(255,255,255,60);
                border-radius: 8px; padding: 6px 14px;
            }
            QPushButton:hover { background: rgba(255, 60, 60, 220); }
            QPushButton:disabled {
                background: rgba(120,120,120,80);
                color: rgba(255,255,255,80);
            }
        """)
        self.btn_cancel.clicked.connect(self.cancel_process)

        btn_row.addWidget(btn_pick, 1)
        btn_row.addWidget(self.btn_cancel)

        # --- прогресс: label + bar ---
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color:#e0e0ff; background:transparent;")
        self.progress_label.setVisible(False)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(0,0,0,120); color: white;
                border: 1px solid #0000ff; border-radius: 6px; text-align: center;
            }
            QProgressBar::chunk { background: #FF7A00; border-radius: 5px; }
        """)

        # --- лог ---
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(
            "background: rgba(0,0,0,120); color:#e0e0ff;"
            "border: 1px solid #0000ff; border-radius: 8px; padding: 6px;"
        )
        self.log_view.setPlaceholderText("Здесь появится распознанный текст…")

        # --- сборка ---
        lay.addWidget(self.drop_frame, 2)
        lay.addLayout(btn_row)                 # ← вместо addWidget(btn_pick)
        lay.addWidget(self.progress_label)
        lay.addWidget(self.progress_bar)
        lay.addWidget(self.log_view, 2)
        return w

    # ---------- Страница: Директории ----------
    def page_directories(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        lbl = QLabel("Папка для сохранения результатов:")
        lbl.setStyleSheet("color: white;")

        self.dir_edit = QLineEdit()
        self.dir_edit.setReadOnly(True)
        cur = self.core.get_output() or "не выбрана"
        self.dir_edit.setText(cur)
        self.dir_edit.setStyleSheet(
            "background: rgba(0,0,0,120); color: white;"
            "border: 1px solid #0000ff; border-radius: 6px; padding: 6px;"
        )

        btn_change = QPushButton("Сменить директорию…")
        btn_change.clicked.connect(self.change_dir)

        lay.addWidget(lbl)
        lay.addWidget(self.dir_edit)
        lay.addWidget(btn_change)
        lay.addStretch()
        return w

    # ---------- Страница: История ----------
    def page_history(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        lbl = QLabel("История обработок (двойной клик — пересобрать XLSX):")
        lbl.setStyleSheet("color: white;")

        self.hist_list = QListWidget()
        self.hist_list.setStyleSheet(
            "background: rgba(0,0,0,120); color:#e0e0ff;"
            "border: 1px solid #0000ff; border-radius: 8px;"
        )
        self.hist_list.itemDoubleClicked.connect(self.repeat_history)

        btn_clear = QPushButton("Очистить историю")
        btn_clear.clicked.connect(self.clear_history)

        btn_refresh = QPushButton("Обновить")
        btn_refresh.clicked.connect(self.refresh_history)

        lay.addWidget(lbl)
        lay.addWidget(self.hist_list, 1)
        lay.addWidget(btn_refresh)
        lay.addWidget(btn_clear)
        self.refresh_history()
        return w

    # ---------- Страница: Профиль ----------
    def page_profile(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        lbl = QLabel("Как программа будет к вам обращаться?")
        lbl.setStyleSheet("color: white;")

        self.name_edit = QLineEdit(self.core.get_name())
        self.name_edit.setStyleSheet(
            "background: rgba(0,0,0,120); color: white;"
            "border: 1px solid #0000ff; border-radius: 6px; padding: 6px;"
        )

        btn_save = QPushButton("Сохранить имя")
        btn_save.clicked.connect(self.save_name)

        lay.addWidget(lbl)
        lay.addWidget(self.name_edit)
        lay.addWidget(btn_save)
        lay.addStretch()
        return w

    # -------------------- Логика --------------------
    def pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение таблицы", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if path:
            self.run_process(path)

    def run_process(self, path: str):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Подождите", "Идёт обработка предыдущего файла")
            return
        self.log_view.clear()
        self.log_view.append(f"⏳ Обработка: {path}")

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_label.setText("Подготовка...")
        self.btn_cancel.setEnabled(True)  # ←

        self.worker = ProcessWorker(self.core, path)
        self.worker.finished_ok.connect(self.on_process_ok)
        self.worker.failed.connect(self.on_process_fail)
        self.worker.cancelled.connect(self.on_process_cancelled)  # ←
        self.worker.progress_changed.connect(self.on_progress)
        self.worker.finished.connect(self._on_worker_finished)  # ←

        self.worker.start()
        self.stack.setCurrentIndex(0)

    def on_progress(self, percent: int, text: str):
        self.progress_bar.setValue(percent)
        self.progress_label.setText(text)

    def on_process_ok(self, text: str):
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.btn_cancel.setEnabled(False)  # ←
        self.log_view.append("✅ Готово\n")
        self.log_view.append(text or "(пусто)")
        self.refresh_history()
    # ---------- Отмена ----------
    def cancel_process(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.btn_cancel.setEnabled(False)
            self.progress_label.setText("⏹ Отмена… подождите завершения текущего шага")

    def on_process_cancelled(self):
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.log_view.append("⏹ Операция отменена пользователем.")

    def _on_worker_finished(self):
        self.btn_cancel.setEnabled(False)
        self.worker = None

    def on_process_fail(self, err: str):
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.btn_cancel.setEnabled(False)  # ←
        self.log_view.append(f"❌ Ошибка:\n{err}")
        QMessageBox.critical(self, "Ошибка", err.splitlines()[0])

    def change_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку сохранений")
        if not path:
            return
        try:
            self.core.set_output(path)
            self.dir_edit.setText(path)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def refresh_history(self):
        self.hist_list.clear()
        for item in self.core.get_history():
            for name, payload in item.items():
                if name == "":
                    continue
                self.hist_list.addItem(f"{name}   ←   {payload[0]}")

    def repeat_history(self, item):
        idx = self.hist_list.row(item)
        history = self.core.get_history()
        # пропускаем служебный {"":[]}
        flat = [h for h in history if list(h.keys()) != [""]]
        if idx >= len(flat):
            return
        name = list(flat[idx].keys())[0]
        path_in, text = flat[idx][name]
        try:
            xlsx_convert(text, path_in)
            QMessageBox.information(self, "Готово", f"XLSX пересобран для {name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def clear_history(self):
        self.core.clear_history()
        self.refresh_history()

    def save_name(self):
        name = self.name_edit.text().strip()
        if not name:
            return
        self.core.set_name(name)
        QMessageBox.information(self, "Готово", f"Имя сохранено: {name}")

    # -------------------- Drag & Drop --------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(10, 10, 80, 200);
                    border: 2px dashed #FF7A00;
                    border-radius: 10px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.drop_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 10, 50, 180);
                border: 2px dashed #0000ff;
                border-radius: 10px;
            }
        """)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and Path(path).is_file():
                self.run_process(path)
                break
        event.acceptProposedAction()
        self.drop_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 10, 50, 180);
                border: 2px dashed #0000ff;
                border-radius: 10px;
            }
        """)

    # -------------------- Перетаскивание окна --------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.title_bar.geometry().contains(event.position().toPoint()):
                self._drag_pos = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton
                and self.title_bar.geometry().contains(event.position().toPoint())):
            self.toggle_max()

    def toggle_max(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)  # ждём до 3 секунд
        super().closeEvent(event)




# -------------------- Точка входа --------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
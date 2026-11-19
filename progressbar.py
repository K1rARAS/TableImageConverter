import os
class progressbar:
    def __init__(self, name, maximum, w, callback=None):
        if maximum <= 0:
            raise ValueError
        self.maximum = maximum
        self.w = w
        self.name = name
        self.count = 0
        self.callback = callback          # ← новое

    def progress(self, value):
        self.count += value
        percent = int(self.count / self.maximum * 100)
        if self.callback:                 # ← новое: GUI-режим
            self.callback(percent, f"{self.name}: {self.count}/{self.maximum}")
            return
        score = int(self.count / self.maximum * self.w)
        self.clear()
        print(
            f"{self.name}\nВыполнено: {self.count}/{self.maximum}\n"
            f"Прогресс задачи {percent}%: {'/' * score}{'.' * (self.w - score)}",
            flush=True,
        )

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")



import os
class progressbar:
    def __init__(self,name , maximum, w):
        if maximum <= 0:
            raise ValueError
        self.maximum = maximum
        self.w = w
        self.name = name
        self.count = 0

    def progress(self,value):
        self.count += value
        percent = int(self.count / self.maximum * 100)
        score = int(self.count / self.maximum * self.w)
        self.clear()
        print(f"{self.name}\nВыполнено: {self.count}/{self.maximum}\nПрогресс задачи {percent}%: {'/'* score}{'.'* (self.w-score)}",flush=True)
    def clear(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')



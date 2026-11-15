from spacetools import ImageTools
from filetools import ftools
from time import sleep
from threading import Thread
import msvcrt, os, sys
from pathlib import Path
from convtools import xlsx_convert
from log import logger

class Terminal:
    def __init__(self):
        self.ft = ftools()
        self.log = logger('app-Terminal',self.ft.get_logger_path())
        self.output = None
        if not self.ft.base.exists() or not self.ft.user.exists():
            task = Thread(target = self.ft.create(), args = ())
            print("Первый запуск...")
            task.start()
            sleep(1)
            print("Создание директорий...")
            sleep(1)
            task.join()
            name = input('Как программа может к вам обращаться? ')
            self.ft.rename(name)
            self.log.info(f'Имя сохранено успешно {name}')
        self.space = ImageTools(self.ft)
        print('Загрузка модели...')
        sleep(2)
        print('Модель успешно загружена...')
        sleep(1)
        self.start()

    def start(self):
        name = self.ft.read_j(self.ft.user)["Name"]
        self.output = self.ft.read_j(self.ft.user)["Output"]
        print(f'Добро пожаловать {name}')
        print('Загрузка меню...')
        sleep(1)
        self.main_menu()

    def clear(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def custom_in(self, name):
        self.clear()
        info = [name,'-'*50,'Поместить сюда: ','-'*50]
        row = info.index('Поместить сюда: ')+1
        col = len(info[2])+1
        for item in info:
            print(item)
        sys.stdout.write(f'\033[{row};{col}H')
        sys.stdout.flush()
        return input()

    def main_menu(self):
        cnt = 1
        running = True
        while running:
            self.clear()
            print("Меню")
            print("1 - Справка\n2 - Профиль\n3 - Директории\n4 - Изображение\n5 - История\n6 - Выйти")
            print(f"Выбрано: {cnt}")
            ch = msvcrt.getch()
            if ch in [b'\x00', b'\xe0']:
                c = msvcrt.getch()
                if c == b'P':
                    cnt += 1
                    if cnt > 6:
                        cnt = 1
                if c == b'H':
                    cnt -= 1
                    if cnt < 1:
                        cnt = 6
            elif ch == b'\r':
                running = False
        if cnt == 1:
            print("Выбор с помощью стрелочек вверх/вниз")
            input("Вернуться в меню...")
            self.main_menu()
        if cnt == 3:
            self.direct()
        if cnt == 4:
            self.image()
        if cnt == 5:
            self.history()
        if cnt == 6:
            self.exit()
        if cnt == 2:
            self.profile()

    def profile(self):
        select = input("Как программа будет к вам обращаться? ")
        self.ft.rename(select)
        self.log.info(f'Имя сохранено успешно {select}')
        print("Успешно сохранено")
        sleep(0.5)
        self.main_menu()

    def direct(self):
        cnt = 1
        running = True
        while running:
            self.clear()
            print("Директории")
            print("1 - Справка\n2 - Изменить директорию\n3 - Вернуться в меню")
            print(f"Выбрано: {cnt}")
            ch = msvcrt.getch()
            if ch in [b'\x00', b'\xe0']:
                c = msvcrt.getch()
                if c == b'P':
                    cnt += 1
                    if cnt > 3:
                        cnt = 1
                if c == b'H':
                    cnt -= 1
                    if cnt < 1:
                        cnt = 3
            elif ch == b'\r':
                running = False
        if cnt == 1:
            print("Выбрана: ",self.ft.read_j(self.ft.user)['Output'])
            input("Вернуться в директории...")
            self.direct()
        if cnt == 2:
            self.change_dir()
        if cnt == 3:
            self.main_menu()

    def change_dir(self):
        select = self.custom_in("Сменить директорию")
        if not select:
            print("Папка не выбрана")
            sleep(1)
            self.direct()
        select = select.strip().strip('"').strip("'").strip()
        if not Path(select).exists():
            print("Такого пути не существует")
            sleep(1)
            self.direct()
        self.ft.rewrite_out(select)
        self.log.info(f'Папка успешно выбрана {select}')
        print("Папка успешно выбрана")
        sleep(0.5)
        self.main_menu()

    def image(self):
        if not Path(self.output).exists():
            print("Папка сохранений не выбрана")
            sleep(1)
            self.main_menu()
        select = self.custom_in("Изображение таблицы")
        if not select:
            print("Изображение не добавлено")
            sleep(1)
            self.main_menu()
        if not Path(select).exists():
            print("Такого пути не существует")
            sleep(1)
            self.direct()
        self.ft.create_out()
        self.space.start(select)
        text = self.space.getresult()
        self.ft.add_history(text,select)
        xlsx_convert(text,select)
        print("Изображение успешно обработано")
        self.main_menu()

    def history(self):
        cnt = 1
        running = True
        while running:
            self.clear()
            print("История")
            print("1 - Справка\n2 - Очистить историю\n3 - Вернуться в меню")
            print(f"Выбрано: {cnt}")
            ch = msvcrt.getch()
            if ch in [b'\x00', b'\xe0']:
                c = msvcrt.getch()
                if c == b'P':
                    cnt += 1
                    if cnt > 3:
                        cnt = 1
                if c == b'H':
                    cnt -= 1
                    if cnt < 1:
                        cnt = 3
            elif ch == b'\r':
                running = False
        if cnt == 1:
            self.look_history()
        if cnt == 2:
            self.clear_history()
        if cnt == 3:
            self.main_menu()

    def look_history(self):
        self.clear()
        history = self.ft.read_j(self.ft.user)["History"]
        if len(history) == 1:
            print("Истории еще нет")
            sleep(1)
            self.history()
        keys = [x for item in history for x in item.keys()]
        for ind, d in enumerate(keys):
            print(f"{ind + 1} — {d}")
            sleep(0.1)
        print('Желаете ли повторить создание таблицы')
        choose = input('Y/n')
        if choose in ['y','Y']:
            select = -1
            while select not in range(2, len(keys)+1):
                try:
                    select = int(input(f'Выберете индекс(2-{len(keys)}): '))
                except ValueError:
                    print('Выберете число:')
            my_history = history[select-1][keys[select-1]]
            xlsx_convert(my_history[0],my_history[1])
        input("Вернуться в меню...")
        self.history()

    def clear_history(self):
        self.ft.delete_history()
        print("История очищена")
        sleep(0.5)
        self.main_menu()

    def exit(self):
        sys.exit()




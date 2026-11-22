import json, sys, os
from pathlib import Path
from log import logger
import shutil

class ftools:
    def __init__(self):
        self.assets = self.get_main('assets')
        self.data = self.get_main('data')
        self.model = self.assets / 'model'
        self.base = self.data / 'Team3' / 'TableImageConverter'
        self.user = self.base / 'User.json'
        self.buffer = self.base / 'buffer'
        self.output = None
        self.logger_path = self.base / 'logs' / 'app.log'
        self.logger = logger('app-filetools', self.get_logger_path())

    def get_main(self, type_assets_or_data:str='assets'):
        is_frozen = getattr(sys,'frozen', False)

        if is_frozen:
            if type_assets_or_data == 'assets':
                meipass = getattr(sys,'_MEIPASS',Path(sys.executable).resolve().parent)
                return Path(meipass).resolve()
            if type_assets_or_data == 'data':
                return Path(os.environ['LOCALAPPDATA']).resolve()

        return Path(__file__).resolve().parent

    def read_j(self,path):
        try:
            with path.open('r',encoding = 'utf-8') as file:
                try:
                    data = json.load(file)
                    return data
                except json.JSONDecodeError:
                    return None
        except FileNotFoundError:
            self.logger.info(f"Файл: {path} не найден")
            return None
        except PermissionError:
            self.logger.info(f"Недостаточно прав {path}")
            return None

    def write_j(self,path, data):
        try:
            with path.open('w',encoding = 'utf-8') as file:
                try:
                    json.dump(data, file, ensure_ascii=False,indent=2)
                    return True
                except TypeError:
                    return None
        except FileNotFoundError:
            self.logger.info(f"Файл: {path} не найден")
            return None
        except PermissionError:
            self.logger.info(f"Недостаточно прав {path}")
            return None

    def read_t(self, path):
        try:
            with path.open('r', encoding='utf-8') as file:
                try:
                    data = file.read()
                    return data
                except:
                    return None
        except FileNotFoundError:
            self.logger.info(f"Файл: {path} не найден")
            return None
        except PermissionError:
            self.logger.info(f"Недостаточно прав {path}")
            return None

    def write_t(self, path, data,choose_w_a = 'w'):
        try:
            with path.open(choose_w_a, encoding='utf-8') as file:
                try:
                    file.write(data)
                    return True
                except TypeError:
                    return None
        except FileNotFoundError:
            self.logger.info(f"Файл: {path} не найден")
            return None
        except PermissionError:
            self.logger.info(f"Недостаточно прав {path}")
            return None

    def get_out(self, path):
        if not path:
            self.logger.info(f"Путь не передан")
            return None
        path_dir = Path(path)
        if path_dir.is_dir():
            output  =  path_dir / 'TIC_output'
            self.logger.info(f"Удалось объявить {path}\TIC_output")
            self.output = output
            self.rewrite_out(output)
            return output
        self.logger.info(f"Не удалось объявить {path}\TIC_output")
        return None

    def get_output(self):
        self.output = self.read_j(self.user)['Output']
        return Path(self.output) / 'TICoutput'

    def get_sub_out(self, path, prefix):
        p = Path(path).stem
        suf = Path(path).suffix
        self.output = Path(self.read_j(self.user)['Output'])
        return str(self.output /'TICoutput'/ (p+prefix+suf))

    def create(self):
        self.base.mkdir(parents = True, exist_ok = True)
        self.logger.info(f"Папка {self.base} успешно создана")
        self.buffer.mkdir(parents = True, exist_ok = True)
        self.logger.info(f"Папка {self.buffer} успешно создана")
        forms = {'Name':"Uknown","Password":"None","Clear_Password":'12345',"Output":str(Path(sys.executable).resolve().parent),"History":[{"":[]}]}
        self.user.touch(exist_ok=True)
        self.logger.info(f"Файл создан, Запись шаблона")
        self.write_j(self.user,forms)

    def create_out(self):
        dir = Path(self.read_j(self.user)['Output'])/'TICoutput'
        if not dir.is_dir():
            dir.mkdir(parents=True,exist_ok=True)
            self.logger.info('Папка создана')
        else:
            self.logger.info('Папка не создана')


    def rewrite_out(self,path):
        user = self.read_j(self.user)
        user["Output"] = str(path)
        self.write_j(self.user,user)

    def get_logger_path(self):
        self.logger_path.parent.mkdir(parents=True,exist_ok = True)
        return self.logger_path

    def rename(self,name):
        user = self.read_j(self.user)
        user["Name"] = name
        self.write_j(self.user,user)
        self.logger.info(f"Имя успешно изменено на: {name}")

    def add_history(self,path_in, text):
        user = self.read_j(self.user)
        history = user['History']
        name = Path(path_in).stem
        new_history = {name:[path_in, text]}
        history.append(new_history)
        user['History'] = history
        self.write_j(self.user,user)
        self.logger.info(f"Добавлено в историю {path_in}")

    def delete_history(self):
        user = self.read_j(self.user)
        user['History'] = [{"":[]}]
        self.write_j(self.user,user)

    def scan(self, path):
        for item in path.glob('*'):
            yield item.resolve()

    def clear_buffer(self):
        shutil.rmtree(str(self.buffer),ignore_errors=True)
        self.buffer.mkdir(parents=True,exist_ok=True)

    def get_output_xlsx(self, path):
        name = Path(path).stem
        return str(Path(self.get_output()) / (name+'.xlsx'))


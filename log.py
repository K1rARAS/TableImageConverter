import logging
from logging.handlers import RotatingFileHandler


def logger(name, log_path):
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)

    if log.handlers:
        return log

    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)8s | %(message)s',
        datefmt="%Y/%m/%d %H:%M:%S"
    )

    file = RotatingFileHandler(
        log_path, maxBytes = 10*1024*1024, backupCount=5,encoding='utf-8'
    )

    file.setLevel(logging.INFO)
    file.setFormatter(formatter)

    log.addHandler(file)
    return log

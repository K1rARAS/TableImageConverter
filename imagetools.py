from deskew import determine_skew
import cv2
import os
import numpy as np
from progressbar import progressbar
from img2table.document import Image as Img2TableImage
import math
import numpy as np
def read_image(image_path: str, flags: int = cv2.IMREAD_COLOR) -> np.ndarray:
    """
    Читает изображение с диска через OpenCV.

    :param image_path: Путь к файлу изображения.
    :param flags: Режим чтения OpenCV:
                  cv2.IMREAD_COLOR     — цветное (BGR), по умолчанию;
                  cv2.IMREAD_GRAYSCALE — оттенки серого;
                  cv2.IMREAD_UNCHANGED — как есть (с альфа-каналом).
    :return: numpy-массив с изображением.
    :raises FileNotFoundError: если файл не существует.
    :raises ValueError: если файл не удалось декодировать как изображение.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Файл не найден: {image_path}")

    # cv2.imread не понимает кириллицу в пути на Windows,
    # поэтому читаем байты через numpy и декодируем из памяти
    try:
        with open(image_path, "rb") as f:
            file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, flags)
    except Exception as e:
        raise ValueError(f"Не удалось прочитать файл {image_path}: {e}") from e

    if img is None:
        raise ValueError(f"Не удалось декодировать изображение: {image_path}")

    return img

def get_angle(path):
    image = cv2.imread(path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Ключевой параметр: angle_pm_90=True поддерживает диапазон ±90°
    angle = determine_skew(gray, angle_pm_90=True)
    return angle

def rotate_no_crop(image_path, angle, background=(255, 255, 255)):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Не удалось открыть изображение: {image_path}")
    old_h, old_w = image.shape[:2]
    angle_rad = math.radians(angle)

    # Вычисление размера холста после поворота
    new_w = abs(np.sin(angle_rad) * old_h) + abs(np.cos(angle_rad) * old_w)
    new_h = abs(np.sin(angle_rad) * old_w) + abs(np.cos(angle_rad) * old_h)

    center = (old_w / 2, old_h / 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    # Смещение матрицы для центрирования содержимого
    M[0, 2] += (new_w - old_w) / 2
    M[1, 2] += (new_h - old_h) / 2

    rotated = cv2.warpAffine(
        image, M, (int(round(new_w)), int(round(new_h))),
        borderValue=background
    )
    return rotated

def process_table_with_custom_ocr(image_path, ocr_instance, output_dir="cells",
                                  keep_files=False, min_cell_size=4):
    """
    image_path: путь к исходному изображению таблицы
    ocr_instance: экземпляр CyrillicOCR (метод .predict(path))
    output_dir: куда сохранять вырезанные ячейки
    keep_files: удалять ли временные файлы после OCR
    min_cell_size: минимальный размер ячейки (px), меньше — пропускаем
    """
    doc = Img2TableImage(image_path)
    extracted_tables = doc.extract_tables(ocr=None)

    if not extracted_tables:
        print("Таблицы не найдены")
        return {}

    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Не удалось открыть изображение: {image_path}")
    h, w = img.shape[:2]

    os.makedirs(output_dir, exist_ok=True)
    results = {}
    all_cells = []  # [(table_idx, row_idx, col_idx, x1, y1, x2, y2), ...]
    for table_idx, table in enumerate(extracted_tables):
        cells = []
        for row_idx, row in enumerate(table.content.values()):
            for col_idx, cell in enumerate(row):
                if cell is None:
                    continue
                x1, y1, x2, y2 = cell.bbox.x1, cell.bbox.y1, cell.bbox.x2, cell.bbox.y2
                x1, y1 = max(0, int(x1)), max(0, int(y1))
                x2, y2 = min(w, int(x2)), min(h, int(y2))
                if x2 - x1 < min_cell_size or y2 - y1 < min_cell_size:
                    continue
                cells.append((row_idx, col_idx, x1, y1, x2, y2))

        cells.sort(key=lambda c: (round(c[3] / 10), c[2]))
        for row_idx, col_idx, x1, y1, x2, y2 in cells:
            all_cells.append((table_idx, row_idx, col_idx, x1, y1, x2, y2))

    pb = progressbar("Распознавание ячеек", len(all_cells), 50) if progressbar else None


    for table_idx, table in enumerate(extracted_tables):
        # Собираем все ячейки с координатами, чтобы отсортировать
        cells = []
        for row_idx, row in enumerate(table.content.values()):
            for col_idx, cell in enumerate(row):
                if cell is None:          # пустая/объединённая ячейка
                    continue
                x1, y1, x2, y2 = cell.bbox.x1, cell.bbox.y1, cell.bbox.x2, cell.bbox.y2
                # Обрезаем по границам изображения
                x1, y1 = max(0, int(x1)), max(0, int(y1))
                x2, y2 = min(w, int(x2)), min(h, int(y2))
                if x2 - x1 < min_cell_size or y2 - y1 < min_cell_size:
                    continue
                cells.append((row_idx, col_idx, x1, y1, x2, y2))

        # Сортируем: сначала по y (строки), потом по x (колонки)
        cells.sort(key=lambda c: (round(c[3] / 10), c[2]))  # грубая группировка по строкам

        for row_idx, col_idx, x1, y1, x2, y2 in cells:
            cell_img = img[y1:y2, x1:x2]
            if cell_img.size == 0:
                continue

            tmp_path = os.path.join(
                output_dir, f"t{table_idx}_r{row_idx}_c{col_idx}.png"
            )
            cv2.imwrite(tmp_path, cell_img)

            try:
                text = ocr_instance.predict(tmp_path)
            except Exception as e:
                print(f"Ошибка OCR для {tmp_path}: {e}")
                text = ""

            results[(table_idx, row_idx, col_idx)] = {
                "text": text,
                "bbox": (x1, y1, x2, y2),
                "file": tmp_path,
            }

            if not keep_files:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

            if pb:
                pb.progress(1)

    return results




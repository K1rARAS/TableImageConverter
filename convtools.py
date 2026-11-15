import pandas as pd
from openpyxl import load_workbook
from io import StringIO
from filetools import ftools
from log import logger
def xlsx_convert(text, path):
    if not text.strip():
        raise ValueError("Пустой результат OCR — таблица не распознана")
    output = ftools().get_output_xlsx(path)
    df = pd.read_csv(StringIO(text), sep="/", header=None)
    df.to_excel(output, index=False, header=False)
    wb = load_workbook(output)
    ws = wb.active
    for col in ws.columns:
        max_len = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2
    wb.save(output)


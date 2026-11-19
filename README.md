
# TableImageConverter (TIC)

A desktop application for recognizing tables from images and converting them into text, with the option to export the result to XLSX.

## About the Program

TableImageConverter is a desktop app with a modern graphical interface designed to extract tabular data from images. The program automatically aligns the image, detects table cells, and recognizes the text within each cell.

## Recognition Model

The core of the program is an OCR model:

- Based on **PP-OCRv6** by PaddlePaddle
- Cyrillic text recognition training by **Metrika Labs**

Contributors: **vladlinv**

> ⚠️ **Current status:** the program is under active development. Known limitations at this stage include:
>
> - Long model loading time at app startup;


## Features

- 🖼️ Upload table images (via drag & drop or file selection dialog);
- 📐 Automatic image alignment (deskew) before processing;
- ✂️ Automatic table segmentation into cells (using img2table);
- 🔤 Cyrillic text recognition in cells;
- 📊 Result assembly into a text format like `text/text/.../text`;
- 📁 Export to XLSX;
- 🕘 Processing history;
- 👤 User profile;
- 🎨 Modern custom UI (dark theme, gradients, movable window).

## Workflow

```text
Image → Alignment → Cell Segmentation → OCR → text/text/.../text
```

- `download()` — the image is aligned based on its skew angle and saved next to the original file as `*_aligned.png`;
- `divide()` — the table is detected and split into individual cells; each cell is processed with OCR;
- `build_text()` — results are assembled into a string like `a/b/c\nd/e/f`.

## Supported Image Formats

- `.png`
- `.jpg` / `.jpeg`
- `.bmp`
- `.tiff`

Files can also be added by dragging and dropping them into the application window.

## Table Limitations

At the current development stage, the program has the following limitations for table processing:

- Minimum cell size is 4 px (smaller cells are skipped);
- The table must be clearly detectable — complex/composite structures, merged cells, and tables without explicit borders may be processed incorrectly;
- The image must be suitable for OCR — low resolution, severe distortions, noise, and artifacts reduce accuracy;
- Image rotation is handled within the range of ±90°;
- Only Cyrillic text is recognized (the model is trained for Cyrillic);
- Multi-line text inside a single cell may be recognized with errors.

## Requirements

- **Python:** ~3.11
- **OS:** Windows (primary target platform; UI and build are oriented toward Windows)

### Main Dependencies

| Library | Purpose |
|---------|---------|
| PyQt6 | Graphical user interface |
| opencv-contrib-python (cv2) | Image processing |
| numpy | — |
| img2table | Table detection and cell segmentation |
| deskew | Skew angle detection |
| progressbar | Progress indication |
| paddleocr + paddlepaddle + paddlex | OCR engine (PP-OCRv6_medium_rec, onnxruntime) |
| openpyxl / xlsxwriter | XLSX export |
| python-bidi, pypdfium2 | Auxiliary OCR dependencies |

## Installation and Launch (from Source)

```bash
pip install -r requirements.txt
python main.py
```

## Project Structure (Main Files)

| File | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `MainWindow.py` | Main window and UI |
| `imagetools.py` | Image utilities (reading, rotation, segmentation) |
| `OCRmodel.py` | OCR model wrapper (CyrillicOCR) |
| `Terminal.py` | Processing pipeline |
| `convtools.py` | XLSX conversion |
| `log.py`, `filetools.py` | Logging and file utilities |
| `model/` | Model files (inference.onnx, etc.) |
| `assets/` | Icons and resources (app.ico) |

## EXE Build (PyInstaller)

To create an executable file, use the following command:

```bash
pyinstaller --onefile --noconsole --name=TIC ^
  --add-data "model;model" ^
  --add-data "assets;assets" ^
  --icon "assets/app.ico" ^
  --collect-all paddlex ^
  --collect-all paddleocr ^
  --collect-all paddle ^
  --collect-data paddle ^
  --collect-binaries paddle ^
  --copy-metadata paddlex ^
  --copy-metadata paddleocr ^
  --copy-metadata paddlepaddle ^
  --hidden-import=bidi ^
  --copy-metadata python-bidi ^
  --copy-metadata pypdfium2 ^
  --copy-metadata opencv-contrib-python ^
  --collect-all opencv-contrib-python ^
  main.py
```

💡 `main.py` includes an error-handling block: when running without a console (`--noconsole`), all errors are written to `error_log.txt` next to the executable file.

## Usage

1. Launch the program;
2. Drag and drop a table image into the window or click "Select File…";
3. Wait for the processing to complete (the progress bar shows the current stage);
4. The recognized text will appear in the log;
5. The result is saved to the selected directory and added to the history;
6. Double-click a history entry to rebuild the XLSX file.

## Contributing

The project is under development, and we welcome feedback and suggestions.

Contributors: **vladlinv**

## License and Acknowledgments

- OCR engine: PaddleOCR (PP-OCRv6, PaddlePaddle);
- Cyrillic model training: Metrika Labs;
- Table detection: img2table;
- Skew detection: deskew;
- License: Apache License.

⚠️ **Note:** the project is a work in progress. Functionality and recognition accuracy may change in future versions.
```
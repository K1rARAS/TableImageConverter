# TableImageConverter (TIC)

A program for recognizing tables from images and converting them to text (with the option to export to XLSX).

## About

**TableImageConverter** is a desktop application with a modern graphical interface designed to extract tabular data from images. The program automatically aligns the image, detects table cells, and recognizes text in each of them.

## Recognition Model

The program is based on the following OCR model:

- Based on **PP-OCRv6** by PaddlePaddle
- Cyrillic text recognition training by **Metrika Labs**

Contributors: **vladlinv**

> ⚠️ **Current status:** the program is under active development. The following known limitations currently exist:
>
> - Slow model loading at application startup;
> - Recognition accuracy is still low and requires improvement.

## Features

- 🖼️ Load table images (drag & drop or via a file selection dialog);
- 📐 Automatic image alignment (deskew) before processing;
- ✂️ Automatic table segmentation into cells (via img2table);
- 🔤 Cyrillic text recognition within cells;
- 📊 Assembly of results into a text format like `text/text/.../text`;
- 📁 Export to XLSX;
- 🕘 Processing history;
- 👤 User profile;
- 🎨 Modern custom interface (dark theme, gradients, draggable window).

## How It Works

```text
Image → Alignment → Cell Segmentation → OCR → text/text/.../text
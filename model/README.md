---
license: apache-2.0
language:
- ru
- kk
- be
- uz
- tg
- uk
- bg
- sr
- tt
- ky
- mn
library_name: PaddleOCR
base_model:
- PaddlePaddle/PP-OCRv6_medium_rec
pipeline_tag: image-to-text
---

<div align="center">
  <img src="https://raw.githubusercontent.com/metrika-labs/PP-OCRv6_rec_cyrillic/master/media/banner.webp" alt="Logo" width="100%"/>
  <br>
  <a href="https://huggingface.co/collections/metrika-labs/cyrillic-ocr"><img src="https://img.shields.io/badge/🤗_Hugging_Face-Cyrillic_OCR-FFD21E" alt="Hugging Face"></a>
  <a href="https://github.com/metrika-labs/PP-OCRv6_rec_cyrillic"><img src="https://img.shields.io/badge/GitHub-PP--OCRv6__rec__cyrillic-181717?logo=github" alt="GitHub"></a>
</div>

## Fast OCR models for printed and handwritten Cyrillic text, based on PP-OCRv6

Results on challenging OCR benchmarks featuring distortions, printing defects, and low-quality images.

<img src="https://raw.githubusercontent.com/metrika-labs/PP-OCRv6_rec_cyrillic/master/media/benchmark-cyrillic.png" alt="Multilingual Cyrillic benchmark" width="50%"/>

<img src="https://raw.githubusercontent.com/metrika-labs/PP-OCRv6_rec_cyrillic/master/media/benchmark-russian.png" alt="Russian-language benchmark" width="100%"/>

Russian-language OCR benchmark: [ru-ocr-benchmark-hard](https://huggingface.co/datasets/metrika-labs/ru-ocr-benchmark-hard)

## Usage

### 🚀 Recommended for CPU (RapidOCR / ONNX)
* [**PP-OCRv6 Medium Cyrillic (RapidOCR)**](https://huggingface.co/metrika-labs/PP-OCRv6_medium_rec_cyrillic_onnx)
* [**PP-OCRv6 Tiny Cyrillic (RapidOCR)**](https://huggingface.co/metrika-labs/PP-OCRv6_tiny_rec_cyrillic_onnx)

### 🚀 Recommended for GPU (PaddlePaddle)
* [**PP-OCRv6 Medium Cyrillic**](https://huggingface.co/metrika-labs/PP-OCRv6_medium_rec_cyrillic)
* [**PP-OCRv6 Tiny Cyrillic**](https://huggingface.co/metrika-labs/PP-OCRv6_tiny_rec_cyrillic)

### Installation

```
pip install rapidocr_onnxruntime huggingface_hub
# For AMD or Intel GPUs: pip install onnxruntime-directml
```

### Full pipeline (Detection + Recognition)

```python
from huggingface_hub import hf_hub_download
from rapidocr_onnxruntime import RapidOCR

# Download the model
model_path = hf_hub_download(repo_id="metrika-labs/PP-OCRv6_medium_rec_cyrillic_onnx", filename="inference.onnx")
keys_path = hf_hub_download(repo_id="metrika-labs/PP-OCRv6_medium_rec_cyrillic_onnx", filename="rec_keys.txt")

# Initialize OCR with standard detection and Cyrillic recognition
ocr = RapidOCR(
    rec_model_path=model_path,
    rec_keys_path=keys_path,
    rec_img_shape=[3, 48, 640],
    # For AMD or Intel GPUs: rec_use_dml=True, det_use_dml=True,
)

_orig_resize = ocr.text_rec.resize_norm_img
ocr.text_rec.rec_image_shape = [3, 48, 48]
ocr.text_rec.resize_norm_img = lambda img, r: _orig_resize(img, max(640 / 48, 1.5 * r))

# Recognize the document
results, _ = ocr("document.jpg")
for bbox, text, score in results:
    print(f"{text} ({score:.4f})")
```

## Details
PP-OCRv6 is a family of fast, lightweight text recognition models from PaddlePaddle. The models were trained by Metrika Labs on 7.5 million varied examples of printed and handwritten text from real document scans and synthetic images.

80% of the examples are in Russian. The other 20% are in Kazakh, Belarusian, Uzbek, Tajik, Ukrainian, Bulgarian, Serbian, Macedonian, Tatar, Kyrgyz, Mongolian, Bashkir, Ossetian, Chuvash, Chechen, Yakut, Avar, and other languages that use Cyrillic.

The models work with PaddleOCR and are also available in ONNX format for fast CPU inference with RapidOCR.

The current version supports handwritten text only in Russian. It reads clear handwriting well, but may make mistakes with cursive or less legible handwriting.


<img src="https://raw.githubusercontent.com/metrika-labs/PP-OCRv6_rec_cyrillic/master/media/sample1.png" alt="Пример 1" width="50%"/><br>
PP-OCRv6 Medium: Мир меняется быстро (score: 0.9882)<br>
PP-OCRv6 Tiny: Пир меняется быстро (score: 0.8412)<br>

## Links

Benchmark for evaluating OCR model quality on Russian text: [metrika-labs/ru-ocr-benchmark-hard](https://huggingface.co/datasets/metrika-labs/ru-ocr-benchmark-hard)

Some handwriting examples come from [AntiplagiatCompany/HWR200](https://huggingface.co/datasets/AntiplagiatCompany/HWR200)

Original PaddleOCR repository: [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)<br>
RapidOCR repository: [RapidAI/RapidOCR](https://github.com/RapidAI/RapidOCR)

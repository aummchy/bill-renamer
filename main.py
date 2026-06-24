import sys
import os
from pathlib import Path

os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def _get_app_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

def _get_bundle_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

sys.path.insert(0, str(_get_bundle_dir() / "src"))

from utils import load_config, get_image_files
from ocr import run_ocr
from extractor import extract_invoice_number, extract_date, extract_name
from renamer import generate_filename, rename_file
from logger import log_rename

def main():
    app_dir = _get_app_dir()
    bundle_dir = _get_bundle_dir()

    config_path = app_dir / "config.json"
    if not config_path.exists():
        config_path = bundle_dir / "config.json"

    config = load_config(config_path)
    input_folder = str(app_dir / config["input_folder"])
    images = get_image_files(input_folder, config["supported_formats"])
    log_dir = str(app_dir / config["log_folder"])
    log_file = config["log_file"]
    print(f"Input: {input_folder}")
    print(f"Found {len(images)} images\n")
    for i, img in enumerate(images, 1):
        print(f"[{i}/{len(images)}] Processing...")
        try:
            max_dim = config.get("max_dimension")
            jpeg_quality = config.get("jpeg_quality", 85)
            resampling = config.get("resampling", "bilinear")
            onnx_threads = config.get("onnx_threads")
            texts, boxes, img_width, img_height = run_ocr(str(img), max_dim, jpeg_quality, resampling, onnx_threads)
            if not texts:
                log_rename(log_dir, log_file, img.name, "N/A", "Failed - No OCR text")
                print(f"  {img.name} -> FAILED: No OCR text")
                continue
            invoice = extract_invoice_number(texts)
            date = extract_date(texts)
            name_filters = config.get("name_filters")
            name = extract_name(texts, boxes, name_filters, img_width, img_height)
            new_name = generate_filename(invoice, date, name, img.suffix)
            result = rename_file(img, new_name)
            log_rename(log_dir, log_file, img.name, result.name, "Success")
            print(f"  {img.name} -> {result.name}")
        except Exception as e:
            log_rename(log_dir, log_file, img.name, "N/A", f"Failed - {e}")
            print(f"  {img.name} -> FAILED: {e}")
    print("\nDone.")

if __name__ == "__main__":
    main()

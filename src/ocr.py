import os
import sys
from pathlib import Path
from PIL import Image
from paddleocr import PaddleOCR

_resampling_map = {
    "nearest": Image.NEAREST,
    "bilinear": Image.BILINEAR,
    "bicubic": Image.BICUBIC,
    "lanczos": Image.LANCZOS,
}

def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent

def _set_model_dir():
    base = _get_base_dir()
    models_dir = base / "models"
    if models_dir.exists():
        os.environ["PADDLE_PDX_CACHE_HOME"] = str(models_dir)

def _create_engine(onnx_threads: int | None = None):
    _set_model_dir()
    engine_config = {}
    if onnx_threads and onnx_threads > 0:
        engine_config["intra_op_num_threads"] = onnx_threads
        engine_config["inter_op_num_threads"] = 1

    return PaddleOCR(
        text_detection_model_name="PP-OCRv6_small_det",
        text_recognition_model_name="PP-OCRv6_small_rec",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        lang="en",
        engine="onnxruntime",
        engine_config=engine_config,
    )

ocr_engine = None

def _get_engine(onnx_threads: int | None = None):
    global ocr_engine
    if ocr_engine is None:
        ocr_engine = _create_engine(onnx_threads)
    return ocr_engine

def run_ocr(image_path: str, max_dimension: int | None = None,
            jpeg_quality: int = 85, resampling: str = "bilinear",
            onnx_threads: int | None = None):
    img = Image.open(image_path).convert("RGB")
    if max_dimension and max(img.size) > max_dimension:
        ratio = max_dimension / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        resample = _resampling_map.get(resampling, Image.BILINEAR)
        img = img.resize(new_size, resample)

    img_width, img_height = img.size

    temp_path = Path(image_path).parent / "_temp_ocr.jpg"
    img.save(temp_path, quality=jpeg_quality)

    try:
        engine = _get_engine(onnx_threads)
        result = engine.predict(str(temp_path))
    finally:
        temp_path.unlink(missing_ok=True)

    if not result or not result[0]:
        return [], [], img_width, img_height

    res = result[0]
    texts = res.get("rec_texts", [])
    boxes = [poly.tolist() for poly in res.get("rec_polys", [])]
    return texts, boxes, img_width, img_height

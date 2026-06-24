import json
from pathlib import Path

def load_config(config_path: str = "config.json") -> dict:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_image_files(folder: str, formats: list[str]) -> list[Path]:
    folder_path = Path(folder)
    if not folder_path.exists():
        raise FileNotFoundError(f"Input folder not found: {folder}")
    files = []
    for f in folder_path.iterdir():
        if f.is_file() and f.suffix.lower() in formats:
            files.append(f)
    return sorted(files)

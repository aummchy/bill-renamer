from pathlib import Path
import re

def sanitize(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def generate_filename(invoice: str, date: str, name: str, ext: str) -> str:
    raw = f"IN_{invoice}_{date}_{name}{ext}"
    return sanitize(raw)

def unique_path(target: Path) -> Path:
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    parent = target.parent
    counter = 1
    while True:
        new_name = f"{stem}({counter}){suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def rename_file(src: Path, new_name: str) -> Path:
    target = unique_path(src.parent / new_name)
    src.rename(target)
    return target

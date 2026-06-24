from pathlib import Path
from datetime import datetime

def log_rename(log_dir: str, log_file: str, original: str, new_name: str, status: str):
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"--------------------------------\n"
        f"Time: {now}\n"
        f"Original: {original}\n"
        f"New: {new_name}\n"
        f"Status: {status}\n"
        f"--------------------------------\n\n"
    )
    filepath = log_path / log_file
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(entry)

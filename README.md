# Bill Renamer

OCR-based invoice/bill auto-renamer. Extracts Invoice Number, Date, and Company Name from scanned invoices using PaddleOCR, then renames files accordingly.

## Requirements

- Windows 10/11
- Python 3.11
- CPU only (no GPU required)
- No internet connection needed (fully offline)

## Installation

```bash
cd bill-renamer
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

1. Place invoice images in the `input_folder` directory (default: `../test-edge`)
2. Run the script:

```bash
python main.py
```

3. Files will be renamed to format: `IN_{InvoiceNumber}_{Date}_{CompanyName}.jpg`
4. Check `logs/rename_log.md` for rename history

## Configuration

Edit `config.json`:

```json
{
  "input_folder": "../test-edge",
  "supported_formats": [".jpg", ".jpeg", ".png"],
  "log_folder": "./logs",
  "log_file": "rename_log.md",
  "max_dimension": 0,
  "jpeg_quality": 100,
  "resampling": "bilinear",
  "onnx_threads": 4,
  "name_filters": {
    "max_length": 30,
    "max_commas": 2,
    "max_numbers": 2,
    "skip_words": ["credit", "note"]
  }
}
```

| Key                        | Description                                                |
| -------------------------- | ---------------------------------------------------------- |
| `input_folder`             | Directory containing invoice images                        |
| `max_dimension`            | Resize images to fit within this dimension (0 = no resize) |
| `jpeg_quality`             | JPEG compression quality (1-100)                           |
| `resampling`               | Resize filter: `nearest`, `bilinear`, `bicubic`, `lanczos` |
| `onnx_threads`             | Number of CPU threads for ONNX Runtime                     |
| `name_filters.max_length`  | Maximum company name length                                |
| `name_filters.max_commas`  | Maximum commas allowed in name                             |
| `name_filters.max_numbers` | Maximum digits allowed in cleaned name                     |
| `name_filters.skip_words`  | Additional words to filter from names                      |

## How It Works

### 1. OCR Processing (`src/ocr.py`)

- Uses PaddleOCR with ONNX Runtime
- Model: PP-OCRv6_small (detection + recognition)
- Returns detected text blocks with bounding box coordinates

### 2. Field Extraction (`src/extractor.py`)

#### Invoice Number

- Searches for "Invoice No" / "Bill No" keywords
- Extracts adjacent alphanumeric value containing digits
- Falls back to standalone 3+ digit numbers

#### Date

- Regex for DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD formats
- Falls back to `dateparser` library
- Returns date in DD-MM-YYYY format

#### Company Name

Multi-stage filtering pipeline:

1. **Basic filters**: Rejects text that is too short, all digits, contains Chinese characters
2. **Skip patterns**: 150+ regex patterns for invoice labels, addresses, product names
3. **Product filter**: Rejects hardware/tech product names (processor, monitor, etc.)
4. **Text filters**: Rejects text with dots, commas, parentheses
5. **Spatial filter**: Only considers text in top 25% of image
6. **Scoring**: Selects candidate with tallest bounding box

### 3. File Renaming (`src/renamer.py`)

- Generates filename: `IN_{InvoiceNumber}_{Date}_{CompanyName}.{ext}`
- Sanitizes names (removes special characters, replaces spaces with underscores)
- Logs all renames to markdown file

## Project Structure

```
bill-renamer/
├── main.py              # Entry point
├── config.json          # Configuration
├── agent.md             # Agent development notes
├── src/
│   ├── __init__.py
│   ├── ocr.py           # PaddleOCR wrapper
│   ├── extractor.py     # Field extraction logic
│   ├── renamer.py       # File renaming
│   ├── utils.py         # Config loading, file discovery
│   └── logger.py        # Rename logging
├── logs/
│   └── rename_log.md    # Rename history
├── models/              # Cached OCR models
└── venv/                # Python virtual environment
```

## Performance

| Model          | Detection | Recognition | Speed (per image) |
| -------------- | --------- | ----------- | ----------------- |
| PP-OCRv6_small | 90.0%     | 85.0%       | ~7s               |

- `jpeg_quality: 100` — pixel-perfect OCR input, negligible speed cost
- `max_dimension: 0` — uses actual image dimensions

## Limitations

- **Supplier name extraction**: Uses bounding box height as proxy for importance. Works well for standard invoices but may fail when:
  - Supplier name has smaller font than other text
  - Invoice has unusual layout (e-Way Bills, multi-page documents)
  - Product names appear in top 25% of image
- **Invoice number format**: Expects standard Indian tax invoice format. May fail for:
  - e-Way Bills (different structure)
  - Invoices without "Invoice No" label
- **Date format**: Only supports DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD

## Known Issues

| File               | Expected          | Actual         | Issue                                   |
| ------------------ | ----------------- | -------------- | --------------------------------------- |
| IN_282_08-05-2026  | SHARMA_ASSOCIATES | Chitra_Talkies | Address text taller than supplier name  |
| IN_132627092032836 | OM_TEXTILES       | AckNo          | e-Way Bill format, not standard invoice |

## License

Internal use only.

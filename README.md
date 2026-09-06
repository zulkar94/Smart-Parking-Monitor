![CI](https://github.com/zulkar94/Smart-Parking-Monitor/actions/workflows/ci.yml/badge.svg)

# Smart Parking Monitor

Python parking system. Detects Bangla + English plates via OpenCV + EasyOCR, normalizes both scripts to one key, assigns nearest free slot, gives turn-by-turn guidance. FastAPI + SQLite backend, live web dashboard.

## Features

- **Plate Recognition**: Bangla & English vehicle plates (OpenCV + EasyOCR)
- **Script Normalization**: Unified key for both Bangla/English plates
- **Slot Assignment**: Nearest available slot with turn-by-turn routing
- **FastAPI Backend**: RESTful API for parking operations
- **Live Dashboard**: Web UI for real-time slot status

## Stack
- Python 3.10+
- FastAPI
- OpenCV, EasyOCR
- SQLite
- JavaScript (frontend)

## Quick Start

```bash
pip install -r requirements.txt
python main.py
# Visit http://localhost:8000
```

## License
MIT

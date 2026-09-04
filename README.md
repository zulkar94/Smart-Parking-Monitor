# Smart Parking Space Monitoring System (Bangla + English ANPR)

Full-stack Python project. Detects license plates (Bangla & English), tracks
free/occupied slots in real time, guides driver to nearest open slot.

## Architecture

```
Camera / Image  -->  Plate Detector (OpenCV/YOLOv8)
                 -->  OCR (EasyOCR: 'bn' + 'en')
                 -->  Plate Normalizer (Bangla digit/script -> canonical code)
                 -->  Parking Manager (SQLite via SQLAlchemy)
                 -->  Guidance Engine (nearest free slot + route hint)
                 -->  FastAPI REST API
                 -->  Web Dashboard (static/index.html, live slot grid)
```

## Why this stack

- **EasyOCR** — only mainstream OCR lib with a trained Bengali (`bn`) model
  bundled, so one pipeline reads both Bangla and English plates without
  swapping engines.
- **OpenCV** — plate localization (edge/contour method for demo; swap in a
  YOLOv8 `.pt` weights file for production-grade detection, hook point is
  `anpr.py::detect_plate_regions`).
- **FastAPI + SQLite/SQLAlchemy** — lightweight, async-friendly, one file DB,
  no infra needed to run locally.
- **Vanilla JS dashboard** — no build step, opens directly in a browser.

## Bangla plate format handled

Bangla plates read e.g. `ঢাকা মেট্রো-গ ১১-১২৩৪` (Dhaka Metro, series গ,
11-1234). The normalizer:
1. Converts Bangla digits (০-৯) to Arabic digits (0-9).
2. Maps common Bangla district/metro name tokens to a transliteration table.
3. Produces a canonical code `DHAKA-METRO-GA-11-1234` used as the DB key, so
   a car photographed once in Bangla and once in English (mixed fleets,
   different camera angles) still matches to the same vehicle record.

English plates (`DHAKA METRO GA 11-1234`, or foreign formats) go through
the same canonicalizer and match directly.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `static/index.html` in a browser (or serve it via any static server) —
it polls `GET /slots` and calls `POST /entry` / `POST /exit` with uploaded
images.

First EasyOCR call downloads the `bn`+`en` model weights (~100MB, one-time,
needs internet).

## API

| Method | Path              | Purpose                                             |
|--------|-------------------|------------------------------------------------------|
| POST   | `/entry`          | Upload plate image → detect, log entry, assign slot |
| POST   | `/exit`           | Upload plate image → detect, free the slot           |
| GET    | `/slots`          | Full lot status (free/occupied per slot)             |
| GET    | `/guide/{plate}`  | Return assigned slot + turn-by-turn hint for a plate |
| GET    | `/logs`           | Recent entry/exit history                            |

## Extending to real cameras

- Replace `detect_plate_regions` in `app/anpr.py` with a YOLOv8 plate model
  (`pip install ultralytics`, load `.pt` weights, feed frames from `cv2.VideoCapture`).
- Point `/entry` and `/exit` at an RTSP/webcam loop instead of file upload —
  the OCR + guidance logic underneath is unchanged.
- Swap the "turn-by-turn hint" string in `parking.py::guidance_text` for
  actual lot-map coordinates if you have a floor plan (row/col already in
  the `ParkingSlot` model).

## Files

```
parking_system/
├── requirements.txt
├── README.md
├── app/
│   ├── database.py   # SQLAlchemy models: ParkingSlot, VehicleLog
│   ├── anpr.py        # plate detection + Bangla/English OCR + normalizer
│   ├── parking.py     # slot assignment, freeing, guidance text
│   ├── schemas.py      # Pydantic response models
│   └── main.py         # FastAPI app & routes
└── static/
    ├── index.html      # dashboard UI
    └── app.js           # polls API, renders slot grid, handles uploads
```

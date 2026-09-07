from typing import List

import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import database as db_models
from . import parking
from . import schemas
from .anpr import canonical_plate_from_image, recognize_plate

app = FastAPI(title="Smart Parking System (Bangla + English ANPR)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    db_models.init_db(num_rows=4, num_cols=5)  # 20-slot demo lot


async def _read_image(file: UploadFile) -> np.ndarray:
    data = await file.read()
    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(400, "Could not decode image")
    return image


@app.post("/entry", response_model=schemas.EntryResultOut)
async def entry(file: UploadFile = File(...), db: Session = Depends(db_models.get_db)):
    image = await _read_image(file)
    raw = recognize_plate(image)
    if not raw:
        raise HTTPException(422, "No plate text detected")
    from .anpr import normalize_plate
    code = normalize_plate(raw)
    if not code:
        raise HTTPException(422, "Plate text could not be normalized")

    slot = parking.assign_slot(db, plate_raw=raw, plate_code=code)
    if slot is None:
        raise HTTPException(409, "Lot is full")

    return schemas.EntryResultOut(
        plate_raw=raw,
        plate_code=code,
        slot_code=slot.code,
        guidance=parking.guidance_text(slot),
    )


@app.post("/exit", response_model=schemas.ExitResultOut)
async def exit_vehicle(file: UploadFile = File(...), db: Session = Depends(db_models.get_db)):
    image = await _read_image(file)
    raw = recognize_plate(image)
    if not raw:
        raise HTTPException(422, "No plate text detected")
    from .anpr import normalize_plate
    code = normalize_plate(raw)

    freed = parking.free_slot(db, plate_code=code)
    return schemas.ExitResultOut(plate_code=code, freed=freed)


@app.get("/slots", response_model=schemas.LotStatusOut)
def slots(db: Session = Depends(db_models.get_db)):
    status = parking.lot_status(db)
    return schemas.LotStatusOut(
        total=status["total"],
        free=status["free"],
        occupied=status["occupied"],
        slots=[schemas.SlotOut.model_validate(s) for s in status["slots"]],
    )


@app.get("/guide/{plate_code}", response_model=schemas.EntryResultOut)
def guide(plate_code: str, db: Session = Depends(db_models.get_db)):
    slot = (
        db.query(db_models.ParkingSlot)
        .filter(db_models.ParkingSlot.plate_code == plate_code.upper())
        .first()
    )
    if slot is None:
        raise HTTPException(404, "Plate not currently parked")
    return schemas.EntryResultOut(
        plate_raw=plate_code,
        plate_code=plate_code.upper(),
        slot_code=slot.code,
        guidance=parking.guidance_text(slot),
    )


@app.get("/logs", response_model=List[schemas.LogOut])
def logs(db: Session = Depends(db_models.get_db), limit: int = 50):
    rows = (
        db.query(db_models.VehicleLog)
        .order_by(db_models.VehicleLog.entry_time.desc())
        .limit(limit)
        .all()
    )
    out = []
    for r in rows:
        out.append(
            schemas.LogOut(
                plate_raw=r.plate_raw,
                plate_code=r.plate_code,
                slot_code=r.slot.code if r.slot else None,
                entry_time=r.entry_time,
                exit_time=r.exit_time,
            )
        )
    return out

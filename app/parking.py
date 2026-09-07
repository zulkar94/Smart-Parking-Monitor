"""Slot assignment, freeing, and driver guidance text."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from . import database as db_models


def find_nearest_free_slot(db: Session) -> Optional[db_models.ParkingSlot]:
    """Nearest = lowest row, then lowest col (closest to the entrance,
    assumed at row 1 / col 1). Swap for a real distance metric if you have
    entrance coordinates per lot layout."""
    return (
        db.query(db_models.ParkingSlot)
        .filter(db_models.ParkingSlot.is_occupied.is_(False))
        .order_by(db_models.ParkingSlot.row.asc(), db_models.ParkingSlot.col.asc())
        .first()
    )


def assign_slot(db: Session, plate_raw: str, plate_code: str) -> Optional[db_models.ParkingSlot]:
    """Log an entry and occupy the nearest free slot. Returns None if full."""
    slot = find_nearest_free_slot(db)
    if slot is None:
        return None

    slot.is_occupied = True
    slot.plate_code = plate_code

    log = db_models.VehicleLog(
        plate_raw=plate_raw,
        plate_code=plate_code,
        slot_id=slot.id,
        entry_time=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(slot)
    return slot


def free_slot(db: Session, plate_code: str) -> bool:
    """Free whichever slot currently holds this plate, close the log entry."""
    slot = (
        db.query(db_models.ParkingSlot)
        .filter(db_models.ParkingSlot.plate_code == plate_code, db_models.ParkingSlot.is_occupied.is_(True))
        .first()
    )
    if slot is None:
        return False

    slot.is_occupied = False
    slot.plate_code = None

    log = (
        db.query(db_models.VehicleLog)
        .filter(db_models.VehicleLog.plate_code == plate_code, db_models.VehicleLog.exit_time.is_(None))
        .order_by(db_models.VehicleLog.entry_time.desc())
        .first()
    )
    if log:
        log.exit_time = datetime.utcnow()

    db.commit()
    return True


def guidance_text(slot: db_models.ParkingSlot) -> str:
    """Simple turn-by-turn hint from the entrance (row 1, col 1) to a slot.
    Replace with real coordinate/path logic if you have a floor plan."""
    if slot.row == 1 and slot.col == 1:
        return f"Slot {slot.code}: straight ahead, first spot on your left."

    directions = []
    if slot.row > 1:
        directions.append(f"drive forward {slot.row - 1} row(s)")
    if slot.col > 1:
        directions.append(f"then {slot.col - 1} bay(s) to the right")
    path = ", ".join(directions) if directions else "straight ahead"
    return f"Slot {slot.code}: {path}."


def lot_status(db: Session):
    slots = db.query(db_models.ParkingSlot).order_by(
        db_models.ParkingSlot.row, db_models.ParkingSlot.col
    ).all()
    free = sum(1 for s in slots if not s.is_occupied)
    return {
        "total": len(slots),
        "free": free,
        "occupied": len(slots) - free,
        "slots": slots,
    }

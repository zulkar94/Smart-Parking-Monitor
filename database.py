"""DB models: parking slots + vehicle in/out logs. SQLite by default."""
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite:///./parking.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ParkingSlot(Base):
    __tablename__ = "parking_slots"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)   # e.g. "A-01"
    row = Column(Integer)                              # for guidance/map
    col = Column(Integer)
    is_occupied = Column(Boolean, default=False)
    plate_code = Column(String, nullable=True)          # canonical plate parked here

    logs = relationship("VehicleLog", back_populates="slot")


class VehicleLog(Base):
    __tablename__ = "vehicle_logs"

    id = Column(Integer, primary_key=True, index=True)
    plate_raw = Column(String)          # raw OCR text (whatever script)
    plate_code = Column(String, index=True)   # canonicalized
    slot_id = Column(Integer, ForeignKey("parking_slots.id"), nullable=True)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)

    slot = relationship("ParkingSlot", back_populates="logs")


def init_db(num_rows: int = 4, num_cols: int = 5):
    """Create tables and seed an empty lot grid if none exists."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(ParkingSlot).count() == 0:
            for r in range(1, num_rows + 1):
                row_letter = chr(ord("A") + r - 1)
                for c in range(1, num_cols + 1):
                    db.add(ParkingSlot(code=f"{row_letter}-{c:02d}", row=r, col=c))
            db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from database.models import Device, PhoneNumber, generate_device_id, generate_password

router = APIRouter(tags=["Application"])


class DeviceOut(BaseModel):
    id: int
    device_id: str
    password: str
    device_connect: str

    class Config:
        from_attributes = True


class PhoneNumberOut(BaseModel):
    id: int
    phone: str
    tg_id: int | None

    class Config:
        from_attributes = True


# 1️⃣ Add a device (defaults to user_id=1)
@router.post("/add-devices", response_model=DeviceOut)
def add_device(db: Session = Depends(get_db)):
    # Get the last ID in the database
    last_id = db.query(func.max(Device.id)).scalar() or 0

    new_device_id = generate_device_id(last_id)
    new_password = generate_password()
    new_device_connect = generate_password(12)  # unique connection code

    device = Device(
        device_id=new_device_id,
        password=new_password,
        device_connect=new_device_connect,
        user_id=1  # 👈 defaults to user_id=1
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


# 2️⃣ Delete a device by ID
@router.delete("/devices/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()

    return {"message": f"Device {device_id} deleted"}


# 3️⃣ Show all phone numbers by device_connect
@router.get("/devices/{device_connect}/phones", response_model=List[PhoneNumberOut])
def get_device_phones(device_connect: str, db: Session = Depends(get_db)):
    phones = db.query(PhoneNumber).filter(PhoneNumber.device_connect == device_connect).all()
    if not phones:
        raise HTTPException(status_code=404, detail="Phone numbers not found")

    return phones


# 4️⃣ Get all devices for user_id=1
@router.get("/my-devices", response_model=List[DeviceOut])
def get_user_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).filter(Device.user_id == 1).all()
    if not devices:
        raise HTTPException(status_code=404, detail="User has no devices")
    return devices

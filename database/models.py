import random
import string

from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


def generate_device_id(last_id):
    suffix = ''.join(random.choices(string.ascii_uppercase, k=3))
    return f"{last_id + 1}{suffix}"


def generate_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, autoincrement=True, primary_key=True)
    tg_id = Column(BigInteger, nullable=False)
    name = Column(String)
    subscription = Column(String, default="basic")
    devices = relationship("Device", back_populates="owner")


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_connect = Column(String(12), nullable=False)  # без ForeignKey
    phone = Column(String, nullable=False)
    tg_id = Column(BigInteger, nullable=True)


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, autoincrement=True, primary_key=True)
    device_id = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    device_connect = Column(String(12), unique=True, nullable=False)

    owner = relationship("User", back_populates="devices")


class SMSHistory(Base):
    __tablename__ = "sms_history"
    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_id = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    message = Column(String, nullable=False)
    eskiz_message_id = Column(String)
    status = Column(String)
    user = relationship("User")


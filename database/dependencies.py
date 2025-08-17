from datetime import datetime, timezone

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from database import get_db
from database.config import SECRET_KEY, ALGORITHM
from database.models import User

# Authorization header orqali tokenni olish
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Токен не валидный!'
        )

    expire = payload.get('exp')
    if not expire:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Токен не содержит дату истечения!'
        )

    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if expire_time < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Срок действия токена истек!'
        )

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Не найден ID пользователя!'
        )

    # Foydalanuvchini bazadan olish
    user = get_exact_user_db(int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Пользователь не найден!'
        )

    return user


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Токен не валидный!'
        )

    expire = payload.get('exp')
    if not expire:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Токен не содержит дату истечения!'
        )

    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if expire_time < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Срок действия токена истек!'
        )

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Не найден ID пользователя!'
        )

    return int(user_id)


def get_exact_user_db(user_id: int):
    db: Session = next(get_db())

    exact_user = db.query(User).filter_by(id=user_id).first()

    if exact_user:
        return {
            "status": 1,
            "message": "Пользователь найден",
            "user": {
                "id": exact_user.id,
                "device_id": exact_user.device_id,
                "tg_id": exact_user.tg_id,
                "subscription": exact_user.subscription,
                "phone_numbers": [pn.phone for pn in exact_user.phone_numbers]
            }
        }
    else:
        return {
            "status": 0,
            "message": "Пользователь не найден"
        }

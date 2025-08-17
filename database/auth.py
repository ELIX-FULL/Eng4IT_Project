from datetime import datetime, timedelta, timezone

from jose import jwt

from database.config import SECRET_KEY, ALGORITHM


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=29)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt

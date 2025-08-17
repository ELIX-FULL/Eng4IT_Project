from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Ссылка для подключения к базе данных PostgreSQL
SQLALCHEMY_DATABASE_URI = 'postgres url connect'

# Подключение к базе данных
engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={'options': '-cclient_encoding=UTF8'})

# Генерация сессий
SessionLocal = sessionmaker(bind=engine)

# Общий класс для моделей
Base = declarative_base()
# Функция для генерации связей к базе данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

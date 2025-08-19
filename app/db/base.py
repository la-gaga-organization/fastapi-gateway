from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Importa i modelli qui sotto per farli vedere ad Alembic
from app.models.user import User  # noqa: E402 F401 ignoro le importazioni fuori ordine e non usate

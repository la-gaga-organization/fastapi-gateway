from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_models():
    from app.models.session import Session  # noqa: E402 F401
    from app.models.token import Token  # noqa: E402 F401
    from app.models.user import User  # noqa: E402 F401

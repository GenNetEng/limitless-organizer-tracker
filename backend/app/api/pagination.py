from sqlalchemy import func, select
from sqlalchemy.orm import Session

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


def paginate(db: Session, model: type, order_by: tuple, limit: int, offset: int) -> tuple[list, int]:
    total = db.scalar(select(func.count()).select_from(model)) or 0
    items = db.query(model).order_by(*order_by).offset(offset).limit(limit).all()
    return items, total

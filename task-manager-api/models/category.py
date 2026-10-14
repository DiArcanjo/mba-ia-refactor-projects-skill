from sqlalchemy import func

from config.settings import DEFAULT_CATEGORY_COLOR
from database.connection import db, utcnow
from models.task import Task


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_CATEGORY_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    @classmethod
    def find(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def list_with_task_count(cls):
        statement = (
            db.select(cls, func.count(Task.id))
            .outerjoin(Task, Task.category_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return db.session.execute(statement).all()

    @classmethod
    def count(cls):
        return db.session.execute(db.select(func.count()).select_from(cls)).scalar()

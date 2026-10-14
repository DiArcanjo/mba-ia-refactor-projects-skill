from sqlalchemy import func
from sqlalchemy.orm import joinedload

from config.settings import CLOSED_STATUSES, DEFAULT_PRIORITY, DEFAULT_TASK_STATUS, STATUS_DONE
from database.connection import db, utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_TASK_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref=db.backref('tasks', cascade='all, delete-orphan'))
    category = db.relationship('Category', backref='tasks')

    def is_overdue(self):
        return (
            self.due_date is not None
            and self.due_date < utcnow()
            and self.status not in CLOSED_STATUSES
        )

    @staticmethod
    def overdue_clause():
        return db.and_(
            Task.due_date.is_not(None),
            Task.due_date < utcnow(),
            Task.status.not_in(CLOSED_STATUSES),
        )

    @classmethod
    def find(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_with_relations(cls):
        statement = (
            db.select(cls)
            .options(joinedload(cls.user), joinedload(cls.category))
            .order_by(cls.id)
        )
        return db.session.execute(statement).scalars().all()

    @classmethod
    def list_by_user(cls, user_id):
        statement = db.select(cls).where(cls.user_id == user_id).order_by(cls.id)
        return db.session.execute(statement).scalars().all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        statement = db.select(cls).order_by(cls.id)
        if text:
            statement = statement.where(
                db.or_(cls.title.like(f'%{text}%'), cls.description.like(f'%{text}%'))
            )
        if status:
            statement = statement.where(cls.status == status)
        if priority is not None:
            statement = statement.where(cls.priority == priority)
        if user_id is not None:
            statement = statement.where(cls.user_id == user_id)
        return db.session.execute(statement).scalars().all()

    @classmethod
    def find_overdue(cls, user_id=None):
        statement = db.select(cls).where(cls.overdue_clause()).order_by(cls.id)
        if user_id is not None:
            statement = statement.where(cls.user_id == user_id)
        return db.session.execute(statement).scalars().all()

    @classmethod
    def count_by_status(cls, user_id=None):
        statement = db.select(cls.status, func.count()).group_by(cls.status)
        if user_id is not None:
            statement = statement.where(cls.user_id == user_id)
        return dict(db.session.execute(statement).all())

    @classmethod
    def count_by_priority(cls, user_id=None):
        statement = db.select(cls.priority, func.count()).group_by(cls.priority)
        if user_id is not None:
            statement = statement.where(cls.user_id == user_id)
        return dict(db.session.execute(statement).all())

    @classmethod
    def count_created_since(cls, moment):
        statement = db.select(func.count()).select_from(cls).where(cls.created_at >= moment)
        return db.session.execute(statement).scalar()

    @classmethod
    def count_done_since(cls, moment):
        statement = (
            db.select(func.count())
            .select_from(cls)
            .where(cls.status == STATUS_DONE, cls.updated_at >= moment)
        )
        return db.session.execute(statement).scalar()

    @classmethod
    def totals_by_user(cls):
        statement = db.select(
            cls.user_id,
            func.count(),
            func.sum(db.case((cls.status == STATUS_DONE, 1), else_=0)),
        ).group_by(cls.user_id)
        return {
            user_id: (total, completed or 0)
            for user_id, total, completed in db.session.execute(statement).all()
        }

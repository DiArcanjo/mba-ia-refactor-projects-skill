import logging
from contextlib import contextmanager

from database.connection import db
from middlewares.error_handler import AppError, PersistenceError

logger = logging.getLogger(__name__)


@contextmanager
def transaction(error_message):
    try:
        yield
        db.session.commit()
    except AppError:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        logger.exception(error_message)
        raise PersistenceError(error_message)

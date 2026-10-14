import os
import secrets

from dotenv import load_dotenv

load_dotenv()

TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
STATUS_DONE = 'done'
CLOSED_STATUSES = (STATUS_DONE, 'cancelled')
DEFAULT_TASK_STATUS = 'pending'
DEFAULT_PRIORITY = 3
MIN_PRIORITY = 1
MAX_PRIORITY = 5
HIGH_PRIORITY_THRESHOLD = 2
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
USER_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
MIN_PASSWORD_LENGTH = 4
DEFAULT_CATEGORY_COLOR = '#000000'
RECENT_ACTIVITY_DAYS = 7
DUE_DATE_FORMAT = '%Y-%m-%d'


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

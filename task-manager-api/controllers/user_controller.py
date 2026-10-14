import logging

from config.settings import DEFAULT_ROLE
from controllers import validators
from controllers.transaction import transaction
from database.connection import db
from middlewares.error_handler import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from models.task import Task
from models.user import User
from services.token_service import generate_token

logger = logging.getLogger(__name__)


def _find_user(user_id):
    user = User.find(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def list_users():
    return User.list_with_task_count()


def get_user(user_id):
    user = _find_user(user_id)
    return user, Task.list_by_user(user_id)


def list_user_tasks(user_id):
    _find_user(user_id)
    return Task.list_by_user(user_id)


def create_user(data):
    if not data:
        raise ValidationError('Dados inválidos')

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', DEFAULT_ROLE)

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')

    validators.validate_email(email)
    validators.validate_password(password, 'Senha deve ter no mínimo 4 caracteres')
    if User.find_by_email(email):
        raise ConflictError('Email já cadastrado')
    validators.validate_role(role)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    with transaction('Erro ao criar usuário'):
        db.session.add(user)
    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return user


def update_user(user_id, data):
    user = _find_user(user_id)
    if not data:
        raise ValidationError('Dados inválidos')

    if 'email' in data:
        validators.validate_email(data['email'])
        existing = User.find_by_email(data['email'])
        if existing and existing.id != user_id:
            raise ConflictError('Email já cadastrado')
    if 'password' in data:
        validators.validate_password(data['password'], 'Senha muito curta')
    if 'role' in data:
        validators.validate_role(data['role'])
    if 'active' in data and not isinstance(data['active'], bool):
        raise ValidationError('Campo active inválido')

    with transaction('Erro ao atualizar'):
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        if 'password' in data:
            user.set_password(data['password'])
        if 'role' in data:
            user.role = data['role']
        if 'active' in data:
            user.active = data['active']
    return user


def delete_user(user_id):
    user = _find_user(user_id)
    with transaction('Erro ao deletar'):
        db.session.delete(user)
    logger.info('Usuário deletado: %s', user_id)


def login(data):
    if not data:
        raise ValidationError('Dados inválidos')

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = User.find_by_email(email) if isinstance(email, str) else None
    if not user or not isinstance(password, str) or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    return user, generate_token(user.id)

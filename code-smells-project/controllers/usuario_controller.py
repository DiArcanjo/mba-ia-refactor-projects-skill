from werkzeug.security import check_password_hash, generate_password_hash

from config.settings import TIPO_USUARIO_PADRAO
from controllers.validators import exigir_dados
from middlewares.auth import gerar_token
from middlewares.error_handler import NotFoundError, UnauthorizedError, ValidationError
from models import usuario_model


def listar(db):
    return usuario_model.listar(db)


def buscar(db, usuario_id):
    usuario = usuario_model.buscar_por_id(db, usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(db, dados):
    dados = exigir_dados(dados)
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not all(isinstance(valor, str) for valor in (nome, email, senha)):
        raise ValidationError("Nome, email e senha devem ser texto")
    return usuario_model.criar(db, nome, email, generate_password_hash(senha), TIPO_USUARIO_PADRAO)


def login(db, dados):
    dados = exigir_dados(dados)
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    credenciais = usuario_model.buscar_credenciais_por_email(db, email) if isinstance(email, str) else None
    if not credenciais or not check_password_hash(credenciais["senha"], str(senha)):
        raise UnauthorizedError("Email ou senha inválidos", incluir_sucesso=True)

    usuario = {chave: credenciais[chave] for chave in ("id", "nome", "email", "tipo")}
    return {**usuario, "token": gerar_token(usuario)}

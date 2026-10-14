import os
import secrets


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    APP_ENV = os.environ.get("APP_ENV", "desenvolvimento")
    APP_VERSION = "1.0.0"
    TOKEN_MAX_AGE = int(os.environ.get("TOKEN_MAX_AGE", "3600"))


CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_PEDIDO_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, STATUS_ENVIADO, STATUS_ENTREGUE, STATUS_CANCELADO]

TIPO_USUARIO_PADRAO = "cliente"
TIPO_USUARIO_ADMIN = "admin"

FAIXAS_DESCONTO = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]

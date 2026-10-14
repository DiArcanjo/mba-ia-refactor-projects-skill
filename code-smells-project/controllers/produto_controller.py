from controllers.validators import exigir_dados, validar_produto
from middlewares.error_handler import NotFoundError, ValidationError
from models import produto_model


def _produto_ou_404(db, produto_id, incluir_sucesso=False):
    produto = produto_model.buscar_por_id(db, produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado", incluir_sucesso)
    return produto


def listar(db):
    return produto_model.listar(db)


def buscar(db, produto_id):
    return _produto_ou_404(db, produto_id, incluir_sucesso=True)


def pesquisar(db, termo, categoria, preco_min, preco_max):
    try:
        preco_min = float(preco_min) if preco_min else None
        preco_max = float(preco_max) if preco_max else None
    except ValueError:
        raise ValidationError("Preço mínimo e máximo devem ser numéricos")
    return produto_model.pesquisar(db, termo, categoria, preco_min, preco_max)


def criar(db, dados):
    campos = validar_produto(exigir_dados(dados), validar_nome_e_categoria=True)
    return produto_model.criar(db, **campos)


def atualizar(db, produto_id, dados):
    _produto_ou_404(db, produto_id)
    campos = validar_produto(exigir_dados(dados), validar_nome_e_categoria=False)
    produto_model.atualizar(db, produto_id, **campos)


def deletar(db, produto_id):
    _produto_ou_404(db, produto_id)
    produto_model.deletar(db, produto_id)

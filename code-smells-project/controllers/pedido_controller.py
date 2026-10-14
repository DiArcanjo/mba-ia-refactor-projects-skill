from config.settings import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PEDIDO_VALIDOS
from controllers.validators import exigir_dados, validar_itens_pedido
from middlewares.error_handler import ValidationError
from models import pedido_model, produto_model
from services import notificacao_service


def criar(db, dados):
    dados = exigir_dados(dados)
    usuario_id = dados.get("usuario_id")
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    itens = validar_itens_pedido(dados.get("itens", []))

    produtos = produto_model.buscar_por_ids(db, {item["produto_id"] for item in itens})
    for item in itens:
        produto = produtos.get(item["produto_id"])
        if produto is None:
            raise ValidationError(f"Produto {item['produto_id']} não encontrado", incluir_sucesso=True)
        if produto["estoque"] < item["quantidade"]:
            raise ValidationError(f"Estoque insuficiente para {produto['nome']}", incluir_sucesso=True)

    total = pedido_model.calcular_total(itens, produtos)
    pedido_id = pedido_model.criar(db, usuario_id, itens, produtos, total)
    notificacao_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_todos(db):
    return pedido_model.listar_todos(db)


def listar_por_usuario(db, usuario_id):
    return pedido_model.listar_por_usuario(db, usuario_id)


def atualizar_status(db, pedido_id, dados):
    dados = exigir_dados(dados)
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")

    pedido_model.atualizar_status(db, pedido_id, novo_status)
    if novo_status in (STATUS_APROVADO, STATUS_CANCELADO):
        notificacao_service.status_pedido_alterado(pedido_id, novo_status)

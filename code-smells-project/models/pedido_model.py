from config.settings import FAIXAS_DESCONTO, STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE
from models import produto_model

SELECT_PEDIDOS_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def _agrupar_pedidos(linhas):
    pedidos = {}
    for linha in linhas:
        pedido = pedidos.setdefault(linha["id"], {
            "id": linha["id"],
            "usuario_id": linha["usuario_id"],
            "status": linha["status"],
            "total": linha["total"],
            "criado_em": linha["criado_em"],
            "itens": [],
        })
        if linha["item_id"] is not None:
            pedido["itens"].append({
                "produto_id": linha["produto_id"],
                "produto_nome": linha["produto_nome"] or "Desconhecido",
                "quantidade": linha["quantidade"],
                "preco_unitario": linha["preco_unitario"],
            })
    return list(pedidos.values())


def listar_todos(db):
    return _agrupar_pedidos(db.execute(SELECT_PEDIDOS_COM_ITENS + " ORDER BY p.id, i.id"))


def listar_por_usuario(db, usuario_id):
    linhas = db.execute(
        SELECT_PEDIDOS_COM_ITENS + " WHERE p.usuario_id = ? ORDER BY p.id, i.id", (usuario_id,)
    )
    return _agrupar_pedidos(linhas)


def calcular_total(itens, produtos):
    total = 0
    for item in itens:
        total += produtos[item["produto_id"]]["preco"] * item["quantidade"]
    return total


def criar(db, usuario_id, itens, produtos, total):
    try:
        pedido_id = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        ).lastrowid
        for item in itens:
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], produtos[item["produto_id"]]["preco"]),
            )
            produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"])
        db.commit()
        return pedido_id
    except Exception:
        db.rollback()
        raise


def atualizar_status(db, pedido_id, novo_status):
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()


def resumo_vendas(db):
    linha = db.execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(total), 0) AS faturamento,
               COALESCE(SUM(status = ?), 0) AS pendentes,
               COALESCE(SUM(status = ?), 0) AS aprovados,
               COALESCE(SUM(status = ?), 0) AS cancelados
        FROM pedidos
        """,
        (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
    ).fetchone()
    return dict(linha)


def calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * taxa
    return 0


def contar(db):
    return db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]


def resetar_dados(db):
    try:
        for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
            db.execute("DELETE FROM " + tabela)
        db.commit()
    except Exception:
        db.rollback()
        raise

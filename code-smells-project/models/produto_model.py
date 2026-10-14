SELECT_PRODUTOS = "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos"


def listar(db):
    return [dict(linha) for linha in db.execute(SELECT_PRODUTOS)]


def buscar_por_id(db, produto_id):
    linha = db.execute(SELECT_PRODUTOS + " WHERE id = ?", (produto_id,)).fetchone()
    return dict(linha) if linha else None


def buscar_por_ids(db, ids):
    ids = list(ids)
    placeholders = ", ".join("?" * len(ids))
    linhas = db.execute(SELECT_PRODUTOS + " WHERE id IN (" + placeholders + ")", ids)
    return {linha["id"]: dict(linha) for linha in linhas}


def pesquisar(db, termo, categoria=None, preco_min=None, preco_max=None):
    filtros, parametros = [], []
    if termo:
        filtros.append("(nome LIKE ? OR descricao LIKE ?)")
        parametros += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        filtros.append("categoria = ?")
        parametros.append(categoria)
    if preco_min:
        filtros.append("preco >= ?")
        parametros.append(preco_min)
    if preco_max:
        filtros.append("preco <= ?")
        parametros.append(preco_max)
    clausula = " WHERE " + " AND ".join(filtros) if filtros else ""
    return [dict(linha) for linha in db.execute(SELECT_PRODUTOS + clausula, parametros)]


def criar(db, nome, descricao, preco, estoque, categoria):
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar(db, produto_id, nome, descricao, preco, estoque, categoria):
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def deletar(db, produto_id):
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()


def baixar_estoque(db, produto_id, quantidade):
    db.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade, produto_id))


def contar(db):
    return db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]

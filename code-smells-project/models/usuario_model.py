SELECT_USUARIOS = "SELECT id, nome, email, tipo, criado_em FROM usuarios"


def listar(db):
    return [dict(linha) for linha in db.execute(SELECT_USUARIOS)]


def buscar_por_id(db, usuario_id):
    linha = db.execute(SELECT_USUARIOS + " WHERE id = ?", (usuario_id,)).fetchone()
    return dict(linha) if linha else None


def buscar_credenciais_por_email(db, email):
    linha = db.execute(
        "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    return dict(linha) if linha else None


def criar(db, nome, email, senha_hash, tipo):
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid


def contar(db):
    return db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]

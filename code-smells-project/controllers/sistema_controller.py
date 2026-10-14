from models import pedido_model, produto_model, usuario_model


def health(db, versao, ambiente):
    db.execute("SELECT 1")
    return {
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produto_model.contar(db),
            "usuarios": usuario_model.contar(db),
            "pedidos": pedido_model.contar(db),
        },
        "versao": versao,
        "ambiente": ambiente,
    }


def resetar_banco(db):
    pedido_model.resetar_dados(db)

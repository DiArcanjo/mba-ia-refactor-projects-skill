import sqlite3

from flask import current_app, g


def abrir_conexao(caminho):
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def get_db():
    if "db" not in g:
        g.db = abrir_conexao(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(_erro=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)

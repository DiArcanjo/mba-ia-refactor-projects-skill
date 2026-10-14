from views.pedido_routes import bp as pedido_bp
from views.produto_routes import bp as produto_bp
from views.sistema_routes import bp as sistema_bp
from views.usuario_routes import bp as usuario_bp


def register_blueprints(app):
    for bp in (produto_bp, usuario_bp, pedido_bp, sistema_bp):
        app.register_blueprint(bp)

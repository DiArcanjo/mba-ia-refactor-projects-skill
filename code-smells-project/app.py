import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Config
from database import connection
from database.schema import init_db
from middlewares.error_handler import register_error_handlers
from views import register_blueprints


def create_app():
    logging.basicConfig(level=logging.INFO)
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    init_db(app.config["DATABASE_PATH"])
    connection.init_app(app)
    register_error_handlers(app)
    register_blueprints(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)

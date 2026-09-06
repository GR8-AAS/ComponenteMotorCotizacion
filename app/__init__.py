from flask import Flask

from app.config import Config


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.routes import motor_calculo_bp
    app.register_blueprint(motor_calculo_bp)

    return app

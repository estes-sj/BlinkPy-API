from flask import Flask
from .routes import bp

def create_app():
    """
    Flask application factory.
    """
    app = Flask(
        __name__,
        static_folder="../media",
        static_url_path="/media"
    )
    app.register_blueprint(bp)
    return app

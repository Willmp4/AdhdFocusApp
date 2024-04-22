from flask import Flask
from .database import db
from .config import configure_app

def create_app():
    app = Flask(__name__)
    configure_app(app)
    db.init_app(app)

    # Import and register routes within the function to avoid circular imports
    from .routes import register_routes
    register_routes(app)

    return app

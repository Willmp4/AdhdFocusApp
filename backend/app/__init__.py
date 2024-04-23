import os
from flask import Flask
from .database import db
from .config import configure_app
from .models import User 
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)
    configure_app(app)
    db.init_app(app)

    # Use environment variable for the JWT secret key
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')

    jwt = JWTManager(app)

    with app.app_context():
        db.create_all()

    from .routes import register_routes
    register_routes(app)
    return app

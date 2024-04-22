def configure_app(app):
    from .secrets import get_database_uri
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
    app.config['SECRET_KEY'] = 'fallback-secret-key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

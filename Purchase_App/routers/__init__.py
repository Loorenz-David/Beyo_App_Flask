from .home import home_bp
from .users import users_bp
from .schemes import schemes_bp
from .s3_routes import s3_routes_bp

def register_blueprints(app):
    app.register_blueprint(home_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(schemes_bp)
    app.register_blueprint(s3_routes_bp)



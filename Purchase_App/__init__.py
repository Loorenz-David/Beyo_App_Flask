import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from datetime import datetime, timedelta
from flask_migrate import Migrate

if os.environ.get('FLASK_ENV') != 'production':
    from dotenv import load_dotenv
    load_dotenv()


db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__) 
    CORS(app,supports_credentials=True,origins=[os.environ.get('FRONT_END_URL')])
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://","postgresql://",1)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    # this disables the event listeners on the modification on database, I might use "signal" later one
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if os.environ.get('FLASK_ENV') == 'production':
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    else:
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

    

    login_manager.init_app(app)
    db.init_app(app)

    login_manager.login_view = 'home_bp.login'

    migrate.init_app(app,db)
   

    from . import models

    with app.app_context():
        pass
        
       
        
       
    
    
    from .routers import register_blueprints
    register_blueprints(app)

    return app
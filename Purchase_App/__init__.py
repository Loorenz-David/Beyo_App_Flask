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
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SECRET_KEY'] = os.environ.get('SECRETE_KEY')

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
        # from .models.Item import Item
        # from .models.Dealer import Dealer
        
        # dea = Dealer.query.get(1)
        # uptd = Item.query.get(5)
        # uptd.dealer = dea
        # db.session.commit()
     

        # 
        # from .models.Item import Item_Notes_Subject
        # subj = Item_Notes_Subject(subject='missing description')
        # db.session.add(subj)
        # db.session.commit()
        # try:

        # from .models.Dealer import Dealer, Dealer_Type
        # type = Dealer(dealer_name='Betty bernader', phone='+40 010101011',email='Betty@email.com',age=40,gender='Female',raw_address='171 45 Solna',coordinates={'lat':59.361549221941154,'lng':18.003097600202825},purchased_count=50000,item_count=400,dealer_type_id=3)
        # db.session.add(type)
        # db.session.commit()

        # from .models.User import Role,User
        # new_role = Role(role='admin',key='some security key',metafields={'keys_tes':'value_test'})
        # db.session.add(new_role)
        # db.session.commit()
        # except Exception as e:
        #     print(e)

        # from .models.query import run_query
        # user_match = run_query('User',{'username':'david'}).first()
        # role_match = run_query('Role',{'role':'admin'}).first()
        # # user_match.roles.append(role_match)
        # # db.session.commit()

        # try:
        #     print(role_match.to_dict())
        # except Exception as e:
        #     print(e)
        # try:
        #     from .models.PUT_models import create_entry,update_object
        #     from .models.DELETE_models import delete_obj
        #     delete_obj('User',{'delition_type':'delete_all','query_filters':{'username':{'operation':'ilike','value':'%test%'}}},verbose=True)
        #     # model_name = 'User'
        #     # role_payload = {'role':'worker','key':'secure key test'}
        #     # user_payload = {'update_type':'first_match' , 'query_filters':{'id':14} , 'values':{'roles':{'action':'unlink','values':{'query_filters':{'id':{'operation':'or','value':[{'operation':'==','value':3},{'operation':'==','value':1}]}},'unlink_type':'unlink_all','fist_match':'unlink_matches'}}}}
        #     # update_object(model_name,user_payload,verbose=True)
        # except Exception as e:
        #     print(e)
        
       
    
    
    from .routers import register_blueprints
    register_blueprints(app)

    return app
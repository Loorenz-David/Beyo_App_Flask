from Purchase_App import db, login_manager
from sqlalchemy  import String
from sqlalchemy.dialects.postgresql import JSONB
from .ModelMixin import ModelMixin
from flask_login import UserMixin



user_roles = db.Table(
                        'user_roles',
                        db.Column('user_id',db.Integer,db.ForeignKey('User.id'),primary_key=True),
                        db.Column('role_id',db.Integer,db.ForeignKey('Role.id'),primary_key=True)
                        
                    )




class User(db.Model,UserMixin,ModelMixin):
    __tablename__ = 'User'
    id = db.Column( db.Integer,primary_key=True)
    username = db.Column(String , nullable=False,unique=True)
    email = db.Column( String, nullable=False, unique=True ,index=True) 
    phone = db.Column( String, nullable=False) 
    password = db.Column( String, nullable=False) 
    profile_picture = db.Column(String) # must change this to JSONB 
    metafields = db.Column(JSONB)
    roles = db.relationship('Role',secondary='user_roles',backref='users')


class Role(db.Model,ModelMixin):
    __tablename__ = 'Role'
    id =  db.Column( db.Integer,primary_key = True)
    role =  db.Column( String,nullable=False,unique=True)
    key =  db.Column( String,nullable=False)
    metafields =  db.Column( JSONB)




  

   

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
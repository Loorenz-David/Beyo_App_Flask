from Purchase_App import db
from sqlalchemy import Integer,String
from sqlalchemy.dialects.postgresql import JSONB
from .ModelMixin import ModelMixin
from datetime import datetime,timezone

class Dealer(db.Model,ModelMixin):
    __tablename__ = 'Dealer'

    id = db.Column(Integer,primary_key=True)

    dealer_type =  db.Column(String,index=True)
    dealer_name = db.Column(String, index=True) 

    phone = db.Column(String) 
    email = db.Column(String, index=True) 
    raw_address = db.Column(String, index=True)
    coordinates = db.Column(JSONB) # give a default dict..
    
    age = db.Column(Integer) 
    gender = db.Column(String) 

    
    dealer_notes = db.relationship('Dealer_Notes',back_populates='dealer')
    
    ## must correct misspeld r in purchased
    puchased_count = db.Column(Integer,index=True) 
    item_count = db.Column(Integer,index=True) 
    
    items = db.relationship('Item',back_populates='dealer')

    created_at = db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc))

    dealer_history =  db.relationship('Dealer_History',back_populates='dealer')



class Dealer_History(db.Model,ModelMixin):
    __tablename__ = 'Dealer_History'

    id = db.Column(Integer,primary_key=True)

    column_name = db.Column(String)
    from_value = db.Column(JSONB)
    to_value = db.Column(JSONB)
    recorder_time = db.Column(db.DateTime,default=lambda:datetime.now(datetime.timezone.utc))
    dealer_id = db.Column(Integer,db.ForeignKey('Dealer.id'))
    dealer = db.relationship('Dealer',back_populates='dealer_history')


class Dealer_Notes(db.Model,ModelMixin):
    __tablename__ = 'Dealer_Notes'

    id = db.Column(Integer,primary_key=True)
    subject = db.Column(String)
    content = db.Column(String)
    created_at = db.Column(db.DateTime,default=lambda:datetime.now(datetime.timezone.utc))
    dealer = db.relationship('Dealer',back_populates='dealer_notes')
    dealer_id = db.Column(Integer,db.ForeignKey('Dealer.id'))


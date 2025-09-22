from Purchase_App import db
from sqlalchemy import String,Integer,Index, event,func,cast,text, inspect,select
from sqlalchemy.dialects.postgresql import JSONB
from .ModelMixin import ModelMixin
from datetime import datetime,timezone
import pprint
from flask import current_app
from sqlalchemy.orm import Session

from .Dealer import Dealer


Items_Notes = db.Table(
    'Items_Notes',
    db.Column('item_id',Integer,db.ForeignKey('Item.id'),primary_key=True),
    db.Column('note_id',Integer,db.ForeignKey('Item_Note.id'),primary_key=True)
)

class Item(db.Model,ModelMixin):
    __tablename__ = 'Item'
    id = db.Column(Integer,primary_key=True)

    article_number = db.Column(String,index=True,nullable=True)
    reference_number = db.Column(String,index=True,nullable=True)


    category = db.Column(String,index=True,nullable=True)
    type = db.Column(String,index=True,nullable=True)

    # some examples of how the properties of the item might look like:

    # CHAIR {structure: backrest upholster / seat upholster, set_of:10, designer:johans}
    # TABLE {structure: round, extentions:outside, extention_count:4, legs: standar}
    properties = db.Column(JSONB,nullable=True)

    # DIMENSIONS {height:200,width:100,depth:40}
    dimensions = db.Column(JSONB,nullable=True)


    # and example of the list of dicts item_issues can hold
    # [{type:scratch, location:upperframe, level: deep}, {type:indent,location:vinil,level:missing}]
    issues = db.Column(JSONB,nullable=True)

    # [{part:leg, count:4},{part:extention,count:2}]
    parts = db.Column(JSONB,nullable=True)

    #[{part:leg,count:1},{part:extention,count:1}]
    missing_parts = db.Column(JSONB,nullable=True)



    #[{subject:missing dimensions, content:'some content'}]
    notes = db.relationship('Item_Note',secondary=Items_Notes,back_populates='items')

    purchased_price = db.Column(Integer,index=True,nullable=True)
    valuation = db.Column(Integer,index=True,nullable=True)
    sold_price = db.Column(Integer,index=True,nullable=True)

    metafields = db.Column(JSONB,nullable=True)


    state = db.Column(String,index=True,nullable=True)

    location = db.Column(String,index=True,nullable=True)

    images = db.Column(JSONB,nullable=True)



    item_history = db.relationship('Item_History',back_populates='item')

    created_at = db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc))
    created_by = db.Column(String,nullable=True)

    dealer_id = db.Column(Integer,db.ForeignKey('Dealer.id'))
    dealer = db.relationship('Dealer',back_populates='items')
    # client_id = db.Column(Integer,db.ForeignKey())



    __table_args__=(

        #properties gin index
        Index(
            'idx_properties_path_ops',
            properties,
            postgresql_using='gin',
            postgresql_ops={'properties':'jsonb_path_ops'}
        ),
        Index(
            'idx_properties_ops',
            properties,
            postgresql_using='gin',
            postgresql_ops={'properties':'jsonb_ops'}
        ),

        #dimensions gin index
        Index(
            'idx_dimensions_path_ops',
            dimensions,
            postgresql_using='gin',
            postgresql_ops={'dimensions':'jsonb_path_ops'}
        ),


        #issues gin index
        Index(
            'idx_issues_path_ops',
            issues,
            postgresql_using='gin',
            postgresql_ops={'issues':'jsonb_path_ops'}
        ),


        #metafields gin index
        Index(
            'idx_metafields_path_ops',
            metafields,
            postgresql_using='gin',
            postgresql_ops={'metafields':'jsonb_path_ops'}
        ),
        Index(
            'idx_metafields_ops',
            metafields,
            postgresql_using='gin',
            postgresql_ops={'metafields':'jsonb_ops'}
        ),

        #missing_parts gin index
        Index(
            'idx_missing_parts_path_ops',
            missing_parts,
            postgresql_using = 'gin',
            postgresql_ops = {'missing_parts':'jsonb_path_ops'}
        ),


    )




class Item_Notes_Subject(db.Model,ModelMixin):
    __tablename__ = 'Item_Notes_Subject'

    id = db.Column(Integer,primary_key=True)
    subject = db.Column(String,index=True)
    notes_counter = db.Column(Integer)
    item_notes = db.relationship('Item_Note',back_populates='subject')

class Item_Note(db.Model,ModelMixin):
    __tablename__ = 'Item_Note'

    id = db.Column(Integer,primary_key=True)
    note_content = db.Column(String)
    creation_time = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc))

    subject_id = db.Column(Integer,db.ForeignKey('Item_Notes_Subject.id'))
    subject = db.relationship('Item_Notes_Subject',back_populates='item_notes')

    items = db.relationship('Item',secondary=Items_Notes,back_populates='notes')




class Item_History(db.Model,ModelMixin):
    __tablename__ = 'Item_History'

    id = db.Column(Integer,primary_key=True)
    column_name = db.Column(String,index=True)
    from_value = db.Column(JSONB)
    to_value = db.Column(JSONB)
    recorded_time = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc))
    item_id = db.Column(Integer,db.ForeignKey('Item.id'))
    item = db.relationship('Item',back_populates='item_history')
    type = db.Column(String, nullable=True,index=True)
    user_name= db.Column(String,nullable=True)


class Item_Stats_Current(db.Model,ModelMixin):
    __tablename__ = 'Item_Stats_Current'

    id = db.Column(Integer,primary_key=True)
    stats_for = db.Column(String,index=True)
    category = db.Column(JSONB)
    type = db.Column(JSONB)


    properties = db.Column(JSONB)
    dimensions = db.Column(JSONB)
    issues = db.Column(JSONB)
    parts = db.Column(JSONB)
    missing_parts = db.Column(JSONB)

    purchased_price = db.Column(Integer)
    valuation = db.Column(Integer)
    sold_price = db.Column(Integer)

    state = db.Column(JSONB)
    location = db.Column(JSONB)


# this following section handles the Creation, Update and Delete of Item_Stats_Current

def update_dealer_counts(dealer_obj, cost_count,item_count,connection):
                     
        dealerUpdateVals = {
            'puchased_count': 
                func.coalesce(Dealer.puchased_count,0) + cost_count ,
            'item_count':
                func.coalesce(Dealer.item_count,0) + item_count
        }
       
        connection.execute(
            Dealer.__table__.update()
            .where(Dealer.id == dealer_obj.id)
            .values(**dealerUpdateVals)
        )

def build_SQL_JSONB(properties_expr,target,multiplier):
     
    
    for key,val in target:
        tempMultiplier = 1 
        if key != 'Set Of':
            tempMultiplier = multiplier
        else:
            if multiplier < 0:
                tempMultiplier = -1
      
        properties_expr = func.jsonb_set(
            properties_expr,
            f'{{{key}}}',
            func.coalesce(
                func.jsonb_extract_path(properties_expr,key),
                text("'{}'::jsonb")
            ),
            True
        )


        properties_expr = func.jsonb_set(
            properties_expr,
            f'{{{str(key)},{str(val)}}}',

            func.to_jsonb(
                func.coalesce(
                    cast(func.jsonb_extract_path_text(properties_expr,key,str(val)),Integer),
                    0
                )+ tempMultiplier
            ),
            True
        )
    return properties_expr

def build_SQL_STR(properties_expr,target,multiplier):
    properties_expr = func.jsonb_set(
                    properties_expr,
                    f'{{{target}}}',
                    func.to_jsonb(
                        func.coalesce(
                            cast(func.jsonb_extract_path_text(properties_expr,target),Integer),
                            0
                        ) + multiplier
                    ),
                    True
                )
    return properties_expr


def update_item_stats(updated_values,connection,id=None,stats_for=None):
    query = Item_Stats_Current.__table__.update()
    default_update_obj = {
        'category':{},
        'type':{},
        'properties':{},
        'dimensions': {},
        'issues': {},
        'parts': {},
        'missing_parts':{},
        'purchased_price': 0,
        'valuation': 0,
        'sold_price': 0,
        'state':{},
        'location':{}
    }
    
    statsObj = Item_Stats_Current.query
    if id is not None:
        statsObj = statsObj.filter_by(id = 1).first()
        if not statsObj:
            default_update_obj['id'] = 1
            default_update_obj['stats_for'] = 'General Stats'
            connection.execute(
                Item_Stats_Current.__table__.insert().values(**default_update_obj)
            )
        query = query.where(Item_Stats_Current.id == id)

    elif stats_for is not None:
        statsObj = statsObj.filter_by(stats_for = stats_for).first()
        if not statsObj:
            default_update_obj['stats_for'] = stats_for
            connection.execute(
                Item_Stats_Current.__table__.insert().values(**default_update_obj)
            )

        query = query.where(Item_Stats_Current.stats_for == stats_for)
    else:
        raise ValueError("You must pass id or stats_for in paramenters")
    
    connection.execute(query.values(**updated_values))
    
def update_item_stats_for_target(target,connection,negative=False,force_multiplier=None,force_type=None,force_category=None):

    update_values = {}
    
  

    multiplier = 1
    if target.category and target.category == 'For Resting':
        if target.properties:
                multiplier = target.properties.get("Set Of", 1)

    if negative:
        if force_multiplier is not None:
            multiplier = force_multiplier

        multiplier *= -1

    if target.purchased_price:
        update_values['purchased_price'] = Item_Stats_Current.purchased_price + (target.purchased_price * multiplier)
    if target.valuation:
        update_values['valuation'] = Item_Stats_Current.valuation + (target.valuation * multiplier)
    if target.sold_price:
            update_values['sold_price'] = Item_Stats_Current.sold_price + (target.sold_price * multiplier)


    if target.state:
        update_values['state'] = func.jsonb_set(
            Item_Stats_Current.state,
            f'{{{target.state}}}',
            func.to_jsonb(
                func.coalesce(
                    cast(Item_Stats_Current.state[target.state].astext,Integer),
                    0
                )+ multiplier
            ),
            True
        )

    if target.location:
        update_values['location'] = func.jsonb_set(
            Item_Stats_Current.location,
            f'{{{target.location}}}',
            func.to_jsonb(
                func.coalesce(
                    cast(Item_Stats_Current.location[target.location].astext,Integer),
                    0
                )+ multiplier
            ),
            True
        )

    if target.category:
        category = target.category
        if force_category is not None:
            category = force_category

        update_values['category'] = func.jsonb_set(
            Item_Stats_Current.category,
            f'{{{category}}}',
            func.to_jsonb(
                func.coalesce(
                    cast(Item_Stats_Current.category[category].astext,Integer),
                    0
                )+ multiplier
            ),
            True
        )

    if target.type:
        type_item = target.type
        if force_type is not None:
            type_item = force_type 
        update_values['type'] = func.jsonb_set(
            Item_Stats_Current.type,
            f'{{{type_item}}}',
            func.to_jsonb(
                func.coalesce(
                    cast(Item_Stats_Current.type[type_item].astext,Integer),
                    0
                )+ multiplier
            ),
            True
        )


    if target.properties:
        properties_expr = Item_Stats_Current.properties
        properties_expr = build_SQL_JSONB(properties_expr,target.properties.items(),multiplier)
        update_values['properties'] = properties_expr
    
    if target.dimensions:
        properties_expr = Item_Stats_Current.dimensions
        properties_expr = build_SQL_JSONB(properties_expr,target.dimensions.items(),multiplier)
        update_values['dimensions'] = properties_expr 

    if target.issues:
        properties_expr = Item_Stats_Current.issues
        for issue in target.issues:
            properties_expr = build_SQL_JSONB(properties_expr,issue.items(),multiplier)
        update_values['issues'] = properties_expr

    if target.parts:
        properties_expr = Item_Stats_Current.parts
        for part in target.parts:
            properties_expr = build_SQL_JSONB(properties_expr,part.items(),multiplier)
        update_values['parts'] = properties_expr 

    if target.missing_parts:
        properties_expr = Item_Stats_Current.missing_parts
        for missing_part in target.missing_parts:
            properties_expr = build_SQL_JSONB(properties_expr,missing_part.items(),multiplier)
        update_values['missing_parts'] = properties_expr 

    update_item_stats(update_values,connection,id=1)

    if target.type:
        type_item = target.type
        if force_type is not None:
            type_item = force_type
        update_item_stats(update_values,connection,stats_for=type_item)

    if target.dealer:
        
        if target.purchased_price: 
        
            val_to_add = target.purchased_price * multiplier

            update_dealer_counts(target.dealer,val_to_add,multiplier,connection)
            
  
  
@event.listens_for(Item,"after_insert")
def after_item_insert(mapper,connection,target):
    try:
        update_item_stats_for_target(target,connection,negative=False)
    except Exception as e:
        print('Stats update failed:' ,e)

  

@event.listens_for(Item,'after_update')
def after_item_update(mapper,connection,target):
    
   
    
    try:

        state = inspect(target)
        jsonb_columns = ['properties','issues','dimensions','missing_parts','parts']
        string_columns = ['state','location']
        integer_columns = ['purchased_price','valuation','sold_price']
        major_columns = ['type','category']

        item_quantity = 1
        old_item_quantity = 1
        old_purchased_count = 0
        updated_old_purchased_count = False
        updated_old_item_quantity = False
        updated_values = {}

        typeState = state.attrs['type']
        type_history = typeState.history
        new_type = None
        old_type = None
        if type_history.has_changes():
            new_type = type_history.added[0]  if type_history.added else None
            old_type = type_history.deleted[0]  if type_history.deleted else None
        
        categoryState = state.attrs['category']
        category_history = categoryState.history
        old_category = None
        if category_history.has_changes():
            old_category = category_history.deleted[0] if type_history.deleted else None

        dealer_history = state.attrs.dealer.history
        has_dealer_changed = dealer_history.has_changes()


        if state.attrs.category.value == 'For Resting':
            target_state = state.attrs.properties
            history_obj = target_state.history

            if target_state.value:
                item_quantity = target_state.value.get('Set Of', 1)
                old_item_quantity = item_quantity

            if history_obj.has_changes():
                
                new_val = history_obj.added[0] if history_obj.added else None
                old_val = history_obj.deleted[0] if history_obj.deleted else None

                if old_val:
                    set_of_diff = new_val.get('Set Of', 1) - old_val.get('Set Of', 1)
                    if set_of_diff != 0:
                        old_item_quantity = old_val.get('Set Of', 1)
                        item_quantity = new_val.get('Set Of', 1)
                        updated_old_item_quantity = True

                

                        properties_expr = getattr(Item_Stats_Current,'type')
                        properties_expr = build_SQL_STR(properties_expr,state.attrs.type.value,set_of_diff)
                        updated_values['type'] = properties_expr

                        properties_expr = getattr(Item_Stats_Current,'category')
                        properties_expr = build_SQL_STR(properties_expr,state.attrs.category.value,set_of_diff)
                        updated_values['category'] = properties_expr

                else:
                    old_item_quantity = 1
        

        if new_type is not None:
            update_item_stats_for_target(target,connection,negative=True,force_multiplier=old_item_quantity,force_type=old_type,force_category=old_category)
            update_item_stats_for_target(target,connection,negative=False,force_multiplier=item_quantity,force_type=new_type)
            return


        for int_col in integer_columns:
            targetState = state.attrs[int_col]
            history_obj = targetState.history
        
            if history_obj.has_changes():
                new_val = history_obj.added[0]  if history_obj.added else 0
                old_val = history_obj.deleted[0] if history_obj.deleted else 0

                diff_item_quantity = 0

                diff = new_val - old_val
            
                new_val = 0

                if updated_old_item_quantity:
                    diff_item_quantity = item_quantity - old_item_quantity
                    new_val = old_val * diff_item_quantity
                    new_val += item_quantity * diff
                else:
                    new_val = diff * item_quantity
                

                if int_col == 'purchased_price':
                    if has_dealer_changed:
                        old_purchased_count = old_val
                        updated_old_purchased_count = True
                    else:
                        update_dealer_counts(target.dealer,new_val,diff_item_quantity,connection)
                
                updated_values[int_col] = getattr(Item_Stats_Current,int_col) + new_val
            elif updated_old_item_quantity:
                diff_item_quantity = item_quantity - old_item_quantity
                new_val = (targetState.value or 0) * diff_item_quantity
                updated_values[int_col] = getattr(Item_Stats_Current,int_col) + new_val

                if int_col == 'purchased_price' and not has_dealer_changed:
                    update_dealer_counts(target.dealer,new_val,diff_item_quantity,connection)

            
        for str_col in string_columns:
            targetState = state.attrs[str_col]
            history_obj = targetState.history
            if history_obj.has_changes():
                new_val = history_obj.added[0] if history_obj.added else None
                old_val = history_obj.deleted[0] if history_obj.deleted else None
                properties_expr = getattr(Item_Stats_Current,str_col)
                if new_val:
                    properties_expr = build_SQL_STR(properties_expr,new_val,item_quantity)
                if old_val:
                    val_to_remove = item_quantity
                    if updated_old_item_quantity:
                        val_to_remove = old_item_quantity

                    properties_expr = build_SQL_STR(properties_expr,old_val,-val_to_remove)
                
                updated_values[str_col] = properties_expr

            elif updated_old_item_quantity:
                diff_item_quantity = item_quantity - old_item_quantity
                properties_expr = getattr(Item_Stats_Current,str_col)
                current_val = targetState.value 
                if current_val:
                    properties_expr = build_SQL_STR(properties_expr,current_val,diff_item_quantity)
                    
                updated_values[str_col] = properties_expr

        for json_col in jsonb_columns:
            targetState = state.attrs[json_col]
            history_obj = targetState.history

            if history_obj.has_changes():
                new_val = history_obj.added[0] if history_obj.added else None
                old_val = history_obj.deleted[0] if history_obj.deleted else None
                properties_expr = getattr(Item_Stats_Current,json_col)

                if isinstance(new_val,list):
                    for val in new_val:
                        properties_expr = build_SQL_JSONB(properties_expr,val.items(),item_quantity)
                else:
                    properties_expr = build_SQL_JSONB(properties_expr,new_val.items(),item_quantity)

                if old_val:
                    val_to_remove = item_quantity
                    if updated_old_item_quantity:
                        val_to_remove = old_item_quantity
                    if isinstance(old_val,list):
                        for val in old_val:
                            properties_expr = build_SQL_JSONB(properties_expr,val.items(),-val_to_remove)
                    else:
                        properties_expr = build_SQL_JSONB(properties_expr,old_val.items(),-val_to_remove)

                updated_values[json_col] = properties_expr

            elif updated_old_item_quantity:
                diff_item_quantity = item_quantity - old_item_quantity
                properties_expr = getattr(Item_Stats_Current,json_col)
                current_val = targetState.value or {}
                if isinstance(current_val,list):
                    for val in current_val:
                        properties_expr = build_SQL_JSONB(properties_expr,val.items(),diff_item_quantity)
                else:
                    properties_expr = build_SQL_JSONB(properties_expr,current_val.items(),diff_item_quantity)
                updated_values[json_col] = properties_expr


        
        

        if has_dealer_changed:
    
            new_dealer = dealer_history.added[0] if dealer_history.added else None
            old_dealer = dealer_history.deleted[0] if dealer_history.deleted else None
    
            if old_dealer:
                val_to_remove = target.purchased_price * item_quantity
                dealer_item_count = item_quantity
        
                if updated_old_item_quantity:
            
                    dealer_item_count = old_item_quantity
                  
                    if updated_old_purchased_count:
                        val_to_remove = old_purchased_count * old_item_quantity
                        
                    else:
                        val_to_remove = target.purchased_price * old_item_quantity
        
                update_dealer_counts(old_dealer, -val_to_remove,-dealer_item_count,connection)
              
            if new_dealer:
                val_to_add = target.purchased_price * item_quantity
        
                update_dealer_counts(new_dealer, val_to_add,item_quantity,connection)

         

        if not updated_values :
            return
        
      

        update_item_stats(updated_values,connection,id=1)
        
        if target.type:
            update_item_stats(updated_values,connection,stats_for=target.type)


    except Exception as e:
        print('update stats failed:', e)
   

@event.listens_for(Item,'after_delete')
def after_item_delete(mapper,connection,target):
 
    update_item_stats_for_target(target,connection,negative=True)


def modify_note_counter(target,connection):
    
    subject_id = target.subject_id
    count_query = select(func.count(Items_Notes.c.item_id))\
        .select_from(Items_Notes.join(Item_Note))\
        .where(Item_Note.subject_id == subject_id)
        
    notes_count = connection.execute(count_query).scalar_one()

    connection.execute(
       Item_Notes_Subject.__table__.update()
       .where(Item_Notes_Subject.id == target.subject_id)
       .values(
           notes_counter = notes_count
       )
    )

   
# @event.listens_for(Item_Note,"after_insert")
# def after_note_added(mapper,connection,target):
#     modify_note_counter(target,connection)

# @event.listens_for(Item_Note,"after_delete")
# def after_note_removed(mapper,connection,target):
#     modify_note_counter(target,connection)

@event.listens_for(Session,'after_flush')
def update_notes_counter(session,flush_context):

    subjects_to_update = set()

    for obj in session.new:
        if isinstance(obj,Item_Note) and obj.subject_id:
            subjects_to_update.add(obj.subject_id)
        
    for obj in session.deleted:
        if isinstance(obj,Item_Note) and obj.subject_id:
            subjects_to_update.add(obj.subject_id)

    for subject_id in subjects_to_update:
       
        
        count_query = select(func.count(Items_Notes.c.item_id))\
            .select_from(Items_Notes.join(Item_Note))\
            .where(Item_Note.subject_id == subject_id)
            
        notes_count = session.execute(count_query).scalar_one()
        print(notes_count,'the count to be added')
        session.execute(
        Item_Notes_Subject.__table__.update()
        .where(Item_Notes_Subject.id == subject_id)
        .values(
            notes_counter = notes_count
        )
        )


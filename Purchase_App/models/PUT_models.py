from Purchase_App import db,models
import re
from Purchase_App.models.query import run_query
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.exc import IntegrityError, DataError, OperationalError
from .models_validation import UnlinkFunctionValidation
from sqlalchemy.inspection import inspect
from sqlalchemy import Integer,String,Float,Boolean,DateTime
from datetime import datetime
models_map = { 
           cls.__name__:cls for cls in models.__dict__.values() if isinstance(cls, type) and issubclass(cls,db.Model)
              }


# {model_name(Role): {'query_filters':{check run query to follow}, link_type(num of objs query returns):first_link  } }
def link_to_relationship(source_obj,user_data,column_name):
   
    for model_name, value in user_data.items():

        query_filters = value.get('query_filters')
        if not query_filters:
            raise Exception(f'"error in function link_to_relationship()" missing key query_filters for column {column_name}')
        link_type = value.get('link_type',None)
        if not link_type:
            raise Exception(f'"error in function link_to_relationship()" No link_type specify in linking with model {model_name} on column {column_name}')

        also_do = value.get('also_do',None)
       
        with db.session.no_autoflush:
            query = run_query(model_name,query_filters).all()
        
        rel = getattr(source_obj,column_name)
        
       
        if len(query) > 0:
            
            if link_type == 'first_link':
                
                if isinstance(rel,InstrumentedList):
                    query = [query[0]]
                else: 
                    query = query[0]
                

            elif link_type == 'all_link':
                if not isinstance(rel,InstrumentedList):
                    query = query[0]
            else:
                raise Exception(f'"error in function link_to_relationship()" invalid link type in key: link_type')

            if rel is None or not isinstance(rel,InstrumentedList):
                setattr(source_obj,column_name,query)
                
            else:
                rel.extend(query)
                
            if also_do:
                for obj in query:
                    fill_object(obj,also_do,commit=False)

        else:
            raise Exception(f'"error in function link_to_relationship()" No object found in model {model_name} when trying to link relationship,column name: {column_name} filters_passed: {value['query_filters']}  ')


#{unlink_type:all_matches / unlink_matches, query_filters: check run_query() guidance,query_matches:'all_matches'/first_match }     
def unlink_relationship(source_obj,user_data,column_name):
    if not hasattr(source_obj,column_name):
        raise Exception(f'"error in function unlink_relationship()" Object {source_obj} has no column {column_name} in model {source_obj.__class__.__name__}')

    validation = UnlinkFunctionValidation().load(user_data)
    unlink = validation['unlink_type']

   
    
    rel = getattr(source_obj,column_name)

    
    if isinstance(rel,InstrumentedList):
        
        if unlink == 'unlink_matches':
            
            query_filters = validation['query_filters']
            query_matches = validation['query_matches']
            
            rel_model_name = source_obj.__class__.__mapper__.relationships.get(column_name).mapper.class_.__name__
            with db.session.no_autoflush:
                list_of_matches = run_query(rel_model_name,query_filters).all()
           
            if len(list_of_matches) > 0:
                if query_matches == 'all_matches':
                    for match_obj in list_of_matches:
                       
                        if match_obj in rel:
                            rel.remove(match_obj)
                        else:
                            raise Exception(f'"error in function unlink_relationship()" Column {column_name} has no relationship with object id: {list_of_matches[0].id}')
                elif query_matches == 'first_match':
                    
                    if list_of_matches[0] in rel:
                        
                        rel.remove(list_of_matches[0])
                        
                    else:
                        raise Exception(f'"error in function unlink_relationship()" Column: {column_name}  has no relationship with object id: {list_of_matches[0].id}')
            else:
                raise Exception(f'["error in function unlink_relationship()" On model {rel_model_name} No objects found with filters: {query_filters}')
            

        elif unlink == 'unlink_all':
            rel.clear()
    else:
        setattr(source_obj,column_name,None)
    
    db.session.add(source_obj)
    db.session.commit()
        

python_to_sqlalchemy = {
    String:str,
    Integer:int,
    Float:float,
    Boolean:bool,
    type(None):type(None),
}

def validate_value_in_column(value,column_name,target_model,mapper=None):
    
    if not mapper:
        mapper = inspect(target_model)
        
    column_to_inspect = mapper.columns.get(column_name,None)
   
    if is_relationship(target_model,column_name,mapper):
        return value
    if column_to_inspect is None:
        raise Exception(f'No column {column_name} in model {target_model.__name__} .')
    
    if column_to_inspect.foreign_keys:
        return value
    
    
    
    
    column_type = column_to_inspect.type
    
    
    try:
        
        expected_type= column_type.python_type
        if expected_type == dict:
            return value
    except NotImplementedError:
        
        expected_type = python_to_sqlalchemy.get(column_type,None)
    
    if expected_type == datetime and isinstance(value,str):
        try:
           value = datetime.fromisoformat(value.replace("Z","+00:00"))
        except Exception :
            try:

                value = datetime.strptime(value,"%a, %d %b %Y %H:%M:%S %Z")
            except Exception as e:
                raise Exception(f'Invalid datetime string {value}, for column {column_name}.')
    
    if value and not isinstance(value,expected_type):
        raise Exception(f'Value "{value}" with type "{type(value)}" is invalid. Column {column_name} accepts value type {expected_type} in model {target_model.__name__}')

    # if type(value) == str and value.strip() == '':
    #     raise Exception(f'Value cannot be empty string in "{column_name}"')

    return value



    

def is_relationship(model,column_name,mapper=None):
    if not mapper:
        mapper = inspect(model)
   
    return column_name in mapper.relationships



def fill_object(target_object,object_values,commit=True,add_session=True,verbose=False,coming_from='Update'):

    target_model = target_object.__class__

    mapper = inspect(target_model)

    required_columns = [ col.name for col in mapper.columns 
                        if  not col.nullable and not col.primary_key and not col.default and not col.server_default]
    collected_columns = []

    for column_name, value in object_values.items():
        isAppend = None
      
        
        if isinstance(value,dict) and  is_relationship(target_model,column_name):

            action = value.get('action')
            values = value.get('values')
            

            if not action or not values:
                raise Exception(f'"error in function fill_object()" no action or values provided in {value}')
            
            if action == 'link':
               
                link_to_relationship(target_object,values,column_name)
               
                continue
            elif action == 'unlink':
                unlink_relationship(target_object,values,column_name)
                continue

            elif action == 'create':
                sub_model_name = value.get('sub_model_name')
                isAppend = value.get('append')
                if not sub_model_name:
                    raise Exception(f'"error in function fill_object()" missing sub_model_name')
            
                value = create_entry(sub_model_name,values,commit=False,verbose=verbose)
               
                if isinstance(getattr(target_object,column_name),InstrumentedList) and not isinstance(value,list):
                    value = [value]
            elif action == 'create_through_rel':

                relVal = getattr(target_object,column_name)
                if isinstance(relVal,InstrumentedList):
                    for obj in relVal:
                        fill_object(obj,values,commit=False)
                elif relVal is not None:
                    fill_object(relVal,values,commit=False)
                continue

                
               
            else:
                raise Exception(f'"error in function fill_object()" invalid action in key: action')
        
     
        value = validate_value_in_column(value,column_name,target_model)

        if isAppend:
            rel = getattr(target_object,column_name)
            if isinstance(rel,InstrumentedList):
                if isinstance(value,list):
                    rel.extend(value)
                else:
                    rel.append(value)
            else:
                raise Exception(f"passed append to column {column_name} but it is not a instrumentedList relationship.")
            
        else:   
            setattr(target_object,column_name,value)

        collected_columns.append(column_name)

        if add_session:
            db.session.add(target_object)

    if coming_from == 'Create':
        if not set(required_columns).issubset(collected_columns):
            missing = set(required_columns) - set(collected_columns)
            raise Exception(f'Missing required vallues {missing} in model {target_model.__name__}')
   
    if commit:
        db.session.commit()
            
        

          

    if verbose:
        print(f''' 
                New Entry created with create_object('object'{target_object},
                                                    'values'{object_values},
                                                    'commit'{commit}
                                                    ) 
               ------------------------------------------------------------------------------                                     
                
              ''')
   
    
    return target_object



   

#Function allows dinamic creation of object in models,
# It takes a model name and a dictionary, 
# the target is to create and entry on the given model, the keys of the dictionary act as column targets on the entry, the values as the value being assign to the column
# if the value is a dictionary it will check the intention, there is two alternatives, create or link.
# when linking, it will find the object or object you will like this new entry to be link to, and link them
# When Creating, It will create an object or objects using the came create_object, this object will be link to the first entry
# for batch creating the object_values must be a list of dicts.

#simple object creation = 
# 
#   { Target_model(User):
#                       {
#                           Column_target('username'):Value('David'),
#                           'Column_tareget('email'):Value('loorenz@gmail.com')
#                        }
#
#
#
#   }

# creating with linking to an existing row = 

#       { Target_model(User):
#                             {
#                                 Column_target('username'):Value('David'),
#                                 'Column_target('email'):Value('loorenz@gmail.com'),
                                
#                                 'Column_target_relationship('roles'):   {
#                                                                         'action''link',
#                                                                         'values': { 
#                                                                                     'Role':{
#                                                                                             'query_filters':'check run_query to build query',
#                                                                                             'link_type':'all_link'
#                                                                                             }

#                                                                                     }
#                                                                         }
#                             }
#         }

# creating entry and creating sub entries = 

#   { Target_model(User):
#                         {
#                             Column_target('username'):Value('David'),
#                             'Column_target('email'):Value('loorenz@gmail.com'),
                            
#                             'Column_target_relationship('roles'):   {
#                                                                     'action''create',
#                                                                     'sub_model_name': 'Role',

#                                                                     'values': { 
                                                                                
#                                                                                 'role':'Admin',
#                                                                                 'key':'some secure key'
                                                                                

#                                                                                 }
#                                                                     }
#                         }
#     }

# when creating sub entries, you can create in batches by passing a list in values.
# each sub entry will be link to the first created entry
#   { Target_model(User):
#                         {
#                             Column_target('username'):Value('David'),
#                             'Column_target('email'):Value('loorenz@gmail.com'),
                            
#                             'Column_target_relationship('roles'):   {
#                                                                     'action''create',
#                                                                     'sub_model_name': 'Role',

#                                                                     'values': [
#                                                                                 {                                                                                 
#                                                                                 'role':'Admin',
#                                                                                 'key':'some secure key'                                                        
#                                                                                 },
#                                                                                 {                                                                                 
#                                                                                 'role':'Marketing',
#                                                                                 'key':'some secure key'                                                        
#                                                                                 },
#                                                                                 ]
#                                                                     }
#                         }
#     }

def create_entry(model_name,user_input,commit=True,verbose=False):
    if not model_name or not user_input:
        raise Exception('"error in function create_entry()" missing model name or object values')
    
    target_model = models_map.get(model_name,None)
    if not target_model:
        raise Exception(f'"error in function create_entry()" No model with name: {model_name}')
    
    new_object_entry = target_model()
  
    new_batch_entry_list =[]
    if isinstance(user_input,list):
      
        for creation_values in user_input:
            new_batch_entry = create_entry(model_name,creation_values,commit=False)
            new_batch_entry_list.append(new_batch_entry)
       
        return new_batch_entry_list
    
    elif not isinstance(user_input,dict):
        raise Exception(f'"error in function create_entry()" Invalid object_values type, when creating object in model {model_name}')

   
    fill_object(new_object_entry,user_input,commit=False,add_session=True,verbose=verbose,coming_from='Create')
    
    if commit:
        db.session.commit()
    
    return new_object_entry
    


# updat

def update_object(model_name,values,update_type,query_filters,commit=True,verbose=False):
   
    target_model = models_map.get(model_name,None)
    if not target_model:
        raise Exception(f'No model with that name: {model_name}')
   
    
    with db.session.no_autoflush:
        query = run_query(model_name,query_filters).all()
        
        if len(query) > 0:
           
            if update_type == 'all_matches':

                for object in query:
                 
                    fill_object(object,values,commit=False,add_session=False,verbose=verbose)
                    

            elif update_type == 'first_match':
                fill_object(query[0],values,commit=False,add_session=False,verbose=verbose)

        else:
            raise Exception(f'[Query Error] No object found with passed filters: {query_filters}')
    
    if commit:
        db.session.commit()
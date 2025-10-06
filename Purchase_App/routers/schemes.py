from Purchase_App import db
from flask import Blueprint, jsonify,request
from flask_login import login_required,current_user
from .responses import build_response
from Purchase_App.models.query import run_query
from Purchase_App.models.PUT_models import create_entry,update_object
from Purchase_App.models.DELETE_models import delete_object
from .schemes_validation import CreateItemsSchema,GetItemsSchema,UpdateItemsSchema,DeleteItemsSchema,ValidationError
from sqlalchemy.exc import IntegrityError, DataError, OperationalError
import re
from datetime import datetime
from token_wraper import token_required

schemes_bp = Blueprint('schemes',__name__,url_prefix='/api/schemes')
# --------------------------------------------------------------------------------
#FOR ALL ERROR MESSAGES I MUST FIND A CONSISTENT FORMAT TO COMUNICATE TO THE FRONT
#I MUST BUILD ALLOW LIST FOR ACCESSING QUERIES, AND MODIFICATIONS TO THE DATA BASE
#ON GET ITEMS QUERY WILL NOT RETURN ALL, I CAN IMPLEMENT PAGINATION IF NEED IT AND FIRST RESULTS
#ON RUN QUERY FUNCTION I HAVE TO IMPLEMENT ORDER BY IS IMPORTANT WHEN IMPLEMENTING WITH PAGINATION
#ON CATCHING ERRORS FROM PSYCOPG2 I INSTEAD OF CHECKING FOR A STRING TEXT I COUL ACCESS THE INSTANCE if isinstance(ie.orig, psycopg2.errors.UniqueViolation):
# THE COMMIT COULD BE DONE OUTSIDE THE FUNCTIONS, IN THE SHECEME ROUTER..
# --------------------------------------------------------------------------------

@schemes_bp.route('/get_items',methods=['GET','POST'])
@token_required
def get_items():
    
   

    body = request.get_json()
    response = build_response()
    status_code = 200

    try:
        
        
        validate = GetItemsSchema().load(body)
    
        model_name = validate['model_name']
        requested_data = validate['requested_data']
        query_filters = validate['query_filters']
        per_page = validate['per_page']
        cursor = validate['cursor']
        
        query = run_query(model_name,query_filters,cursor)

        if per_page:
            query = query.limit(per_page).all()
        else:
            query = query.all()
    

        if len(query) > 0:
            unpack_data = [ obj.to_dict(requested_data) for obj in query]
            
            response = build_response(200,'Data adquired.',unpack_data)
            status_code = 200
            
        else:
            raise Exception(f'[Exception Error] No objects found in model {model_name} with filters: {query_filters}')

    except ValidationError as ve:
        response = build_response(400,'[Validation Error] Invalid data for for request.',server_message=str(ve))
        status_code = 400
        print(ve,'val')

    except IntegrityError as ie:
        response =build_response(400,f'[Database Ingerity Error] Constrain faild on query.',server_message=str(ie))
        status_code = 400
        db.session.rollback()
        print(ie,'in')

    except DataError as de:
        db.session.rollback()
        response =build_response(400,f'[Database Data Error] Invalid data type or value when quering.',server_message=str(de))
        print(de)

    except OperationalError as oe:
        db.session.rollback()
        response =build_response(400,f'[Database Operational Error] DB error ocurred when querying.',server_message=str(oe))
        status_code = 400
        print(oe,'op')

    except Exception as e:
        response = build_response(400,'[Exception Error] Error on query.', server_message=str(e))
        status_code = 400
        db.session.rollback()
        print(e,'ex')
    
    return jsonify(response), status_code 


@schemes_bp.route('/create_items',methods=['POST'])
@token_required
def create_items():
    body = request.get_json()
    response = build_response()
    status_code = 200
    
    
    
    try:
        
        
        def creation_call(item):
            
            validated = CreateItemsSchema().load(item)
            model_name = validated['model_name']
            requested_data = validated['requested_data']
            object_values = validated['object_values']
            reference = validated['reference']

            
            create_new_entry = create_entry(model_name,object_values)

            obj_data = []
            if isinstance(create_new_entry,list):
                obj_data = [obj.to_dict(requested_data)for obj in create_new_entry]
            else:
                obj_data = [create_new_entry.to_dict(requested_data)]

            

            return {'reference':reference,'obj_data':obj_data}

        if isinstance(body,list):
            
            list_of_obj_data = []
            reference = ''
            for item in body:
                creation = creation_call(item)
                list_of_obj_data.append(creation['obj_data'])
                reference = creation['reference']

            response = build_response(201,f"{reference} created !", body=list_of_obj_data)
            status_code = 201
        elif isinstance(body,dict):
            
            creation = creation_call(body)
            response = build_response(201,f"{creation['reference']} created !", body=creation['obj_data'])
            status_code = 201
        else:
            raise Exception('Incorrect body format, it should be list of dicts or dict.')

       

    except ValidationError as ve:
        response = build_response(400,f"[Validation Error] Invalid data for {body.get('reference','entry')}.",server_message=ve.messages)
        status_code = 400

    except IntegrityError as ie:
        
        error_msg = str(ie)
        message = f"[Database Ingerity Error] Constrain faild on {body.get('reference','entry')}."
        if 'duplicate key value violates unique constraint' in error_msg:
            match = re.search(r'Key \((\w+)\)=\((.*?)\)',error_msg) 
            if match:
                match_field = match.group(1)
                match_value = match.group(2)
                message = f"[Database Ingerity Error] The value '{match_value}' for field -{match_field}- alreade exist. Please choose another. "
                
        elif '(psycopg2.errors.NotNullViolation)' in error_msg:
            match = re.search(f'value in column "([^"]+)"',error_msg)
            if match:
                match_value = match.group(1)
                message = f'[Database Ingerity Error] -{match_value}- cannot be empty.'
            
        
        response = build_response(400,message,server_message=str(ie))
        status_code = 400
        db.session.rollback()

    except DataError as de:
        
        response =build_response(400,f"[Database Data Error] Invalid data type or value when creating {body.get('reference','entry')}.",server_message=str(de))
        status_code = 400
        db.session.rollback()

    except OperationalError as oe:
        
        response =build_response(400,f"[Database Operational Error] DB error ocurred when creating {body.get('reference','entry')}.",server_message=str(oe))
        status_code = 400
        db.session.rollback()

    except Exception as e:
        
        response = build_response(400,f"[Exception Error] Error creating {reference}.", server_message=str(e))
        status_code = 400
        db.session.rollback()
    
    return jsonify(response), status_code


@schemes_bp.route('/update_items',methods=['POST'])
@token_required
def update_items():
    body = request.get_json()
    response = build_response()
    status_code = 200
    
    try:
        

        def update_call(body):
            validation = UpdateItemsSchema().load(body)
            model_name = validation['model_name']
            object_values = validation['object_values']
            reference = validation['reference']
            query_filters = validation['query_filters']
            update_type = validation['update_type']
            update_object(model_name,object_values,update_type,query_filters)

            return  {'reference':reference}
       
        if isinstance(body,list):
            reference = ''

            for item in body:
                update = update_call(item)
             
                reference = update['reference']

            response = build_response(201,f'{reference} Updated!')
            status_code = 201
            

        elif isinstance(body,dict):
            update = update_call(body)
            response = build_response(201,f"{update['reference']} Updated!")
            status_code = 201
        else:
            raise Exception('Incorrect body format, it should be list of dicts or dict.')


    except ValidationError as ve:
        response = build_response(400,f"[Validation Error] Invalid Data for {body.get('reference','entry')}.",server_message=str(ve))
        status_code = 400
    except IntegrityError as ie:
       
        error_msg = str(ie)
        message = "[Database Ingerity Error] Constrain faild on {body.get('reference','entry')}."
        if 'duplicate key value violates unique constraint' in error_msg:
            match = re.search(r'Key \((\w+)\)=\((.*?)\)',error_msg) 
            if match:
                match_field = match.group(1)
                match_value = match.group(2)
                message = f"[Database Ingerity Error] The value '{match_value}' for field -{match_field}- alreade exist. Please choose another. "
                
        elif '(psycopg2.errors.NotNullViolation)' in error_msg:
            match = re.search(f'value in column "([^"]+)"',error_msg)
            if match:
                match_value = match.group(1)
                message = f'[Database Ingerity Error] -{match_value}- cannot be empty.'
            
        
        response = build_response(400,message,server_message=str(ie))
        status_code = 400
        db.session.rollback()

    except DataError as de:
        db.session.rollback()
        response =build_response(400,f"[Database Data Error] Invalid data type or value when updating {body.get('reference','entry')}.",server_message=str(de))
        status_code = 400

    except OperationalError as oe:
        db.session.rollback()
        response =build_response(400,f"[Database Operational Error] DB error ocurred when updating {body.get('reference','entry')}.",server_message=str(oe))
        status_code = 400

    except Exception as e:
        db.session.rollback()
        print(e)
        response = build_response(400,f'[Exception Error] Error Updating .', server_message=str(e))
        status_code = 400
    
    return jsonify(response), status_code

@schemes_bp.route('/delete_items',methods=['POST'])
@token_required
def delete_items():
    body = request.get_json()
    response = build_response()
    status_code = 200
    print(body,'the body that was received when deleting item')
    try:
       
        def delete_call(body):
            validation = DeleteItemsSchema().load(body)
            model_name = validation['model_name']
            object_values = validation['object_values']
            reference = validation['reference']

            delete_object(model_name,object_values)
            print(reference,'....')
            return {'reference':reference}
        
        if isinstance(body,list):
            reference = ''
            for item in body:
                delete = delete_call(item)
                reference = delete['reference']
            response = build_response(201,f'{reference} Deleted!')
            status_code = 201
        elif isinstance(body,dict):
            delete = delete_call(body)
            response = build_response(201,f"{delete['reference']} Deleted!")
            status_code = 201
            print(response,'response fom delition')

    except ValidationError as ve:
        response = build_response(400,f"[Validation Error] Invalid data for {body.get('reference','entry')}.",server_message=str(ve))
        status_code = 400

    except IntegrityError as ie:
        db.session.rollback()
        response =build_response(400,f"[Database Ingerity Error] Constrain faild on {body.get('reference','entry')}.",server_message=str(ie))
        status_code = 400

    except DataError as de:
        db.session.rollback()
        response =build_response(400,f"[Database Data Error] Invalid data type or value when deleting {body.get('reference','entry')}.",server_message=str(de))
        status_code = 400

    except OperationalError as oe:
        db.session.rollback()
        response =build_response(400,f"[Database Operational Error] DB error ocurred when deleting {body.get('reference','entry')}.",server_message=str(oe))
        status_code = 400


    except Exception as e:
        db.session.rollback()
        response = build_response(400,f"[Exception Error] Error Deleting {reference}.", server_message=str(e))
        status_code = 400
    
    return jsonify(response), status_code
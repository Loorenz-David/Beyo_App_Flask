from flask import Blueprint\
,render_template,jsonify  \
,request
from werkzeug.security import generate_password_hash,check_password_hash
from Purchase_App.models.query import run_query
from flask_login import login_required,login_user,current_user,logout_user
from .responses import build_response

home_bp = Blueprint('home',__name__) 

@home_bp.route('/api',methods=['POST','GET'])
def home():
    
    response = build_response()
    status_code = 200

    payload = request.get_json(silent=True)
    unpack_columns = None
    if payload:
        unpack_columns = payload.get('requested_data',None)

    try:
        if(current_user.is_authenticated):
            data = []
            if unpack_columns:
                data.append(current_user.to_dict(unpack_columns)) 

            response = build_response(200,'user is authenticated.',body=data)
            status_code = 200
            
        else:
            response = build_response(401,'user not authenticated')
            status_code = 401
    except Exception as e:
        response = build_response(500,'Server Error', server_message=str(e))
        status_code= 400
    return jsonify(response),status_code





@home_bp.route('/api/login',methods=['POST'])
def login():
    
    body = request.get_json()
   
    reponse = build_response()
    status_code = 200
    
    try:

        user_email = body.get('email')
        user_pass = body.get('password')
        user_info_request = body.get('request_info',['username',{'roles':['role','id']},'profile_picture'])

        if not user_email:
            raise Exception(f'missing email')
        elif not user_pass:
            raise Exception(f'missing pass')

        user_match = run_query('User',{'email':user_email}).first()
        if not user_match:
            raise Exception(f'No User found with email: {user_email}')
        
        if user_pass != user_match.password:
            raise Exception(f'Incorrect password.')
            
        
        login_user(user_match)


        user_info = [user_match.to_dict(user_info_request)]
       

        response = build_response(200,'user login!',body=user_info)
        status_code = 200
    
    except Exception as e:
        print('exception _-------')
        print(Exception)
        response = build_response(400,'incorrect login',server_message=str(e))
        status_code = 401
    
    
    return jsonify(response),status_code


@home_bp.route('/api/logout',methods=['POST'])
@login_required
def logout():
    reponse = build_response()
    status_code = 200
    
    try:
        logout_user()
        response = build_response(200,'User logged out')
        
    except Exception as e:
        response = build_response(400,'Erro loging out',server_message=str(e))
        status_code = 400

    return jsonify(response),status_code

@home_bp.route('/register',methods=['POST'])
def register():
    
    required_for_registration = ['username','email','phone']
    body = request.get_json()
    
    







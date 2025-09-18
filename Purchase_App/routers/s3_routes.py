from flask import Blueprint,request,jsonify
from flask_login import login_required
import boto3
import os
from dotenv import load_dotenv
from .responses import build_response

load_dotenv()

s3_routes_bp = Blueprint('s3_routes',__name__)

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRETE_ACCESS_KEY = os.getenv('AWS_SECRETE_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET = os.getenv('S3_BUCKET')


def initialize_s3_client():
    s3_client = boto3.client("s3",
                         region_name=AWS_REGION,
                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRETE_ACCESS_KEY)
    return s3_client


@s3_routes_bp.route("/api/generate-presigned-url",methods=['POST'])
@login_required
def generate_presigned_url():

    payload = request.get_json()

    list_of_files = payload
    print(list_of_files,'in s3 router')

    response = build_response()
    status_code = 200
    
    try:

        if not list_of_files:
            raise Exception('Missing file name or file type') 

        s3_client = initialize_s3_client()

        list_of_urls =[]

        required_keys = ['fileName','filePath','fileType']
        for file_dict in list_of_files:
            print(file_dict)
            if not all(key in required_keys for key in file_dict) :
                raise Exception("Missing required keys shoul contain -filename-,-filePath-,fileType")

            url = s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket":S3_BUCKET,
                    "Key":f"{file_dict['filePath']}/{file_dict['fileName']}",
                    "ContentType":file_dict['fileType']
                   
                },
                ExpiresIn=120
            )
            print(file_dict['fileType'],'checking file type on upload')
            list_of_urls.append({'url':url,'fileName':file_dict['fileName']})

        response= build_response(200,'url access created',body=list_of_urls)
        
        
    except Exception as e:
        response = build_response(400,'somthing went wrong',server_message=str(e))
        status_code = 400

    return jsonify(response),status_code


@s3_routes_bp.route('/api/delete-image-url',methods=['POST'])
@login_required
def remove_image_url():

    payload = request.get_json()
    urls = payload.get('urls')

    if not urls or len(urls) == 0:
        return(jsonify(build_response(400,'Missing urls key or list is empty'))),400

    deleted_urls = []
    try:
        s3_client = initialize_s3_client()
        
        for url in urls:
            
            key = url.split(f".amazonaws.com/")[-1]

            s3_client.delete_object(
                Bucket = S3_BUCKET,
                Key = key
            )
            deleted_urls.append(url)
           

        return jsonify(build_response(201, f"{len(urls)} Image deleted")),201
        
    except Exception as e:

        
        return jsonify(build_response(400,'Something went wrong deleting from the cloud',body=deleted_urls, server_message=str(e))), 400
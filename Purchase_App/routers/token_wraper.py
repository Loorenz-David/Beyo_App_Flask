from functools import wraps

from flask import request, jsonify, Flask   
import jwt
import datetime 
import os


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Token missing"}), 401
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
            request.user_email = payload['email']
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


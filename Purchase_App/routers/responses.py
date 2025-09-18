

def build_response(status=200,message='response return no data',body=[],server_message=''):
    response_dict = {'status':status,
                     'body':body,
                     'message':message,
                     'server_message':server_message}
    return response_dict
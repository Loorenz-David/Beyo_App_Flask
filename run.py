from Purchase_App import create_app
app = create_app()

if __name__ == '__main__':
    import os
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(debug=True,port=5001,
            ssl_context=('certs/cert.pem','certs/key.pem'))
    else:
        app.run(host='0.0.0.0',port=8080)
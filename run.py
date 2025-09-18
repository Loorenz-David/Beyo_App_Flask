from Purchase_App import create_app

if __name__ == '__main__':
    app = create_app()

    app.run(debug=True,port=5001,
            ssl_context=('certs/cert.pem','certs/key.pem'))
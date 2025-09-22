from Purchase_App import create_app,db
from sqlalchemy import text, inspect

app = create_app()

# with app.app_context():
#     try:
#         result = db.session.execute(text('SELECT current_database();'))
#         db_name = result.fetchone()[0]
#         print('connected to database: ', db_name)
#         print (result)

#         inpector =inspect(db.engine)
#         tables = inpector.get_table_names()
#         print('tables in database: ', tables)
#         print(dir(inpector))

#     except Exception as e:
#         print('Faild to connect: ', e)
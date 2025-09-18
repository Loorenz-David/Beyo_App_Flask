from Purchase_App import models,db
from Purchase_App.models.query import run_query
from Purchase_App.models.PUT_models import fill_object

models_map = { cls.__name__:cls for cls in models.__dict__.values() if isinstance(cls, type) and issubclass(cls,db.Model)}


#{query_filters:{check run_query for guidance}, delition_type:delete_all }
def delete_object(model_name,user_data,commit=True,verbose=False):

    target_model = models_map.get(model_name,None)
     
    if not target_model:
        raise Exception(f'"error in function delete_object()" No model with name: {model_name}')
    
    query_filters = user_data.get('query_filters',None)
    also_do = user_data.get('also_do',None)

    if not query_filters:
        raise Exception(f'"error in function delete_object()" No query_filters in body')
    query = run_query(model_name,query_filters).all()

    if len(query) == 0:
        raise Exception(f'"error in function delete_object()" No object found in model {model_name} with filters: {query_filters}')

    delition_type = user_data.get('delition_type')
    if not delition_type:
        raise Exception(f'"error in function delete_object()" missing key: deletion_type')
    
    if delition_type == 'delete_all':
        for obj in query:
            if also_do:
                fill_object(obj,also_do,commit=False)
            db.session.delete(obj)
    elif delition_type == 'delete_first':
        
        if also_do:
                fill_object(query[0],also_do,commit=False)

        db.session.delete(query[0])
        
    else:
         raise Exception(f'"error in function delete_object()" Invalid delition type on deletion_type')

    if verbose:
        print(f'Deleting object {query} !!')

    if commit:
        db.session.commit()
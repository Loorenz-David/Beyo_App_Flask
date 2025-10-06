from Purchase_App import models
from Purchase_App import db
from sqlalchemy import or_, and_

models_map = {  cls.__name__: cls for cls in models.__dict__.values() if isinstance(cls, type) and issubclass(cls,db.Model)
            }



def get_dict_value(d,key,message,required=True):

    if not isinstance(d,dict):
        if required:
            raise Exception(message)
        else:
            return False

    val = d.get(key,None)
    if val == None:
       
        raise Exception(message)
    return val

def get_attr_or_fail(obj,attr,message):

    if not hasattr(obj,attr):
        raise Exception(message)
    
    return getattr(obj,attr)




# this function return a filter operation base on operation pass in operation, some examples on how the query dict should be structure:
# operation = '>' : 
#                   {
#                    column: {
#                              operation:'>',value:'the value you want to compare'
#                            }
#                   }

# operation = 'range': 
#                       {
#                           column: {
#                                       operation:'range',value:{
#                                                                 'start':'value starts at','end':'value ends at'
#                                                                }
#                                   }
#                       }

# operation = 'or': {
#                     column: {
#                               operation:'or',value:[
#                                                      {
#                                                        operation:'range',value:{
#                                                                                   'start':'value starts at','end':'value ends at'
#                                                                                 }
#                                                        },
#                                                     ]
#                               }
#                       }


def get_filter(target_column,operation,value):
    
    operations_dict = {'==':lambda: target_column == value,
                       '!=':lambda: target_column != value,
                       '>':lambda: target_column > value,
                       '>=':lambda:  target_column >= value,
                       '<':lambda:  target_column < value,
                       '<=':lambda:  target_column <= value,
                       'like':lambda:  target_column.like(value),
                       'ilike':lambda:  target_column.ilike(value),
                       'in':lambda:  target_column.in_(value if isinstance(value,list) else [value]),
                       'notin':lambda:  ~target_column.in_(value if isinstance(value,list) else [value]),
                       'range':lambda: target_column.between(value['start'],value['end']),
                       'or':lambda: or_(*[get_filter(target_column,cond['operation'],cond['value']) for cond in value if 'operation' in cond and 'value' in cond]),
                       'and':lambda: and_(*[get_filter(target_column,cond['operation'],cond['value']) for cond in value if 'operation' in cond and 'value' in cond]),
                       'contains': lambda: target_column.contains(value),
                       'contained_by':lambda: target_column.contained_by(value),
                       'has_key':lambda: target_column.has_key(value),
                       'has_any':lambda: target_column.has_any(value),
                       'has_all':lambda: target_column.has_all(value),
                       }

    filter_func = operations_dict.get(operation)
    if not filter_func:
        raise Exception(f'"error in function get_filter()" invalid operator: {operation}')
    
    
    return filter_func()




# query_dict = {column_target_name:{'operation':'==','value':'some value'}}
# for queries in relationships, use . notation, if User has a relationship set to roles you will do roles.name
# it can go further into nested relationships examplet roles.permissions.target_column
def run_query(model_name,query_dict,cursor=None):
    
    target_model = get_dict_value(models_map,model_name,f'"error in function run_query()" No Model found with name: {model_name}',required=True)

   
    query = db.session.query(target_model)
    joined_relationships = set()
    
    
    and_filters = []
    or_filters = []
   
    for key, condition in query_dict.items():
        
        target_column = None
        append_style = 'and'
        
        if 'or-' in key:
            key = key.replace('or-','')
            append_style = 'or'
        

        if '.' in key:

            path_parts = key.split('.')
            current_model = target_model

            for i in range(len(path_parts) -1):
                rel_name = path_parts[i]
                rel_key = f'{current_model.__name__}.{rel_name}'
                
                if rel_key not in joined_relationships:
                    query = query.join(getattr(current_model,rel_name))
                    joined_relationships.add(rel_key)
                
                current_model = getattr(current_model,rel_name).property.mapper.class_
            
            final_column = path_parts[-1]
            target_column = get_attr_or_fail(current_model,final_column,f'"error in function run_query()" No column with name {final_column} in model {current_model.__name__}')
            
        else:
            target_column = get_attr_or_fail(target_model,key, f'"error in function run_query()"In model{model_name} No column found with name: {key}')
         
        
        operation = get_dict_value(condition,'operation',f'"error in function run_query()" a dict was recieved but no operation key was given: {condition}',required=False)
        if operation:
            value = condition.get('value',None)
            if value == None:
                raise Exception(f'no value was given in dict {condition}')
           
            adquired_filter =   get_filter(target_column,operation,value)
            if append_style == 'or':
                or_filters.append(adquired_filter)
            else:
                and_filters.append(adquired_filter)
        else:
            if condition == None:
                raise Exception(f'"error in function run_query()" condition is None, it should be some target value or a dict with an  operation and target value')

            adquired_filter = (target_column == condition)

            if append_style == 'or':
                or_filters.append(adquired_filter)
            else:
                and_filters.append(adquired_filter)

    final_filters = None
   
    if or_filters  and and_filters:
        final_filters = and_(*and_filters,or_(*or_filters))
    elif or_filters:
        final_filters = or_(*or_filters)
    elif and_filters:
        final_filters = and_(*and_filters)
    

  
    if final_filters is not None:
        query = query.filter(final_filters)

    query = query.order_by(target_model.id.desc())
    
    
    if cursor:
        query = query.filter(target_model.id < cursor)

    
    return query
   

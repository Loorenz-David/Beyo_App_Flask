from sqlalchemy.orm.collections import InstrumentedList



# to dict unpacks the given object, with the columns specify in list, it can access to relationships by passing
# a dict instead of a string, the key is the target column and the value can be a dict again or a list of columns
# ['col1','col2',{'col-relationship':['col1','col2']}]
class ModelMixin():


    def to_dict(self,columns_to_unpack,set_of_observations=None):
        unpack_data = {}

        if set_of_observations == None:
            set_of_observations = set()
        
        if isinstance(columns_to_unpack,list):
            for column in columns_to_unpack:
                print(column,'the column being unpacked')
                if isinstance(column,dict):
                    for key, values in column.items():
                        
                        if key in set_of_observations:
                            raise Exception(f"passed duplicate column in dictionary: {key}")
                        
                        if not hasattr(self,key):
                            raise ValueError(f"no relation with name: {key}")
                        
                        target_relation = getattr(self,key)
                        set_of_observations.add(key)
                        
                        if isinstance(target_relation,InstrumentedList):
                            list_of_relations = []
                            for obj in target_relation:
                                list_of_relations.append(obj.to_dict(values))
                            unpack_data[key] = list_of_relations
                        else:
                            unpack_data[key] = target_relation.to_dict(values)

                else:
                
                    if not hasattr(self,column):
                        raise ValueError(f"{column} is not a valid attribute (column name) of {self.__class__.__name__}")
                    if column in set_of_observations:
                        raise Exception(f"passed duplicate column in list: {column}")
                    
                    set_of_observations.add(column)
                    unpack_data[column] = getattr(self,column)
        else:
            raise Exception(f"columns passed must be wrap in list: [ <-- {columns_to_unpack} --> ] ")
        
        return unpack_data
    
    

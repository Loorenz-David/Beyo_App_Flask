from marshmallow import Schema,fields,validate, ValidationError

class GetItemsSchema(Schema):
    model_name = fields.Str(required=True)
    requested_data = fields.List(fields.Raw(),required=True)
    query_filters = fields.Dict(required=False,load_default=dict)
    per_page = fields.Int(required=False,load_default=None)
    cursor = fields.Int(required=False,load_default=None)
    

class CreateItemsSchema(Schema):
    model_name = fields.Str(required=True)
    requested_data = fields.List(fields.Raw(),required=False)
    object_values = fields.Raw(required=True)
    reference = fields.Str(required=True)

class UpdateItemsSchema(Schema):
    model_name = fields.Str(required=True)
    object_values = fields.Dict(required=True)
    reference = fields.Str(required=True)
    query_filters = fields.Dict(required=True)
    update_type = fields.Str(required=True)
    


class DeleteItemsSchema(Schema):
    model_name = fields.Str(required=True)
    object_values = fields.Raw(required=True)
    reference = fields.Str(required=True)
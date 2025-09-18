from marshmallow import Schema,fields,validate, ValidationError


class UnlinkFunctionValidation(Schema):
    unlink_type = fields.Str(required=True)
    query_filters = fields.Dict(required=True)
    query_matches = fields.Str(required=True)
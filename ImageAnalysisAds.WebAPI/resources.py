# -*- coding: utf-8 -*-

from models import Image, Label
from db import session
from flask_restful import reqparse, abort, Resource, fields, marshal_with

image_fields = {
    'id': fields.Integer,
    'url': fields.String,
    'obj': fields.String
    #'create_at': fields.String,
    #'create_by': fields.String
}

label_fields = {
    'url': fields.String,
    'obj': fields.String
    #'create_at': fields.String,
    #'create_by': fields.String
}

parser = reqparse.RequestParser()
parser.add_argument('id')
parser.add_argument('url')
parser.add_argument('obj')
#parser.add_argument('create_at')
#parser.add_argument('create_by')


class ImageResource(Resource):
    @marshal_with(image_fields)
    def get(self, id):
        img = session.query(Image).filter(Image.id == id).first()
        if not img:
            abort(404, message="Image {} doesn't exist".format(id))
        return img

    def delete(self, id):
        img = session.query(Image).filter(Image.id == id).first()
        if not img:
            abort(404, message="Image {} doesn't exist".format(id))
        session.delete(img)
        session.commit()
        return {}, 204

    @marshal_with(image_fields)
    def put(self, id):
        parsed_args = parser.parse_args()
        img = session.query(Image).filter(Image.id == id).first()
        img.obj = parsed_args['obj']
        session.add(img)
        session.commit()
        return img, 201
    
    @marshal_with(image_fields)
    def post(self):
        parsed_args = parser.parse_args()
        img = Image(obj=parsed_args['obj'], url=parsed_args['url'])
                    #create_at=parsed_args['create_at'], create_by=parsed_args['create_by'])
        session.add(img)
        session.commit()
        return img, 201


class LabelResource(Resource):
    
    @marshal_with(label_fields)
    def get(self, obj):
        label = session.query(Label).filter(Label.obj == obj).first()
        if not label:
            abort(404, message="Label {} doesn't exist".format(obj))
        return label

    @marshal_with(label_fields)
    def post(self):
        parsed_args = parser.parse_args()
        label = Label(obj=parsed_args['obj'], url=parsed_args['url'])
                    #create_at=parsed_args['create_at'], create_by=parsed_args['create_by'])
        session.add(label)
        session.commit()
        return label, 201
    
class LabelListResource(Resource):
    @marshal_with(label_fields)
    def get(self):
        labels = session.query(Label).all()
        return labels
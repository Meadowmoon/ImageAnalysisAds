from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps
from image import Image
from label import Label

db_connect = create_engine('sqlite:///chinook.db')
app = Flask(__name__)
api = Api(app)

api.add_resource(Image, '/image') # Route_1
api.add_resource(Label, '/label') # Route_2

if __name__ == '__main__':
     app.run()
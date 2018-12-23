from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
from resources import *

app = Flask(__name__)
api = Api(app)

api.add_resource(ImageResource, '/imageads/v1.0/images/<string:id>', endpoint='img') 
api.add_resource(LabelResource, '/imageads/v1.0/labels/<string:obj>', endpoint='label')
api.add_resource(LabelListResource, '/imageads/v1.0/labels', endpoint='labels')

'''
CREATE TABLE IF NOT EXISTS images (
 id INTEGER PRIMARY KEY,
 url TEXT NOT NULL,
 obj TEXT NULL
);
        
CREATE TABLE IF NOT EXISTS labels (
 obj TEXT PRIMARY KEY,
 url TEXT NOT NULL
);

curl -i http://localhost:5002/imageads/v1.0/labels/cup
curl -i http://localhost:5002/imageads/v1.0/images/1
curl -i -H "Content-Type: application/json" -X POST -d '{"obj":"cup", "url":"resource/label/starbucks.png"}' http://localhost:5002/imageads/v1.0/labels
'''

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(port=5002)
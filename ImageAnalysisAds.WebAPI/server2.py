from flask_restful import Api
from resources import *

from threading import Thread
from PIL import Image
import numpy as np
import flask
import redis
import uuid
import time
import json
import io
import base64
import os
import tensorflow as tf
import sys



# initialize our Flask application, Redis server
sys.path.append('../ImageAnalysisAds.Mapper/')
from overlayImage import *
app = flask.Flask(__name__)
db = redis.StrictRedis(host="localhost", port=6379, db=0)
model = None
detection_graph = None

#app = Flask(__name__)
api = Api(app)

api.add_resource(ImageResource, '/imageads/v1.0/images/<string:id>', endpoint='img') 
api.add_resource(LabelResource, '/imageads/v1.0/labels/<string:obj>', endpoint='label')
api.add_resource(LabelListResource, '/imageads/v1.0/labels', endpoint='labels')

def load_image_into_numpy_array(image):
    print(image)
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
            (im_height, im_width, 3)).astype(np.uint8)
def base64_encode_image(a):
    return base64.b64encode(a).decode("utf-8")

def base64_decode_image(a, dtype, shape):
	# if this is Python 3, we need the extra step of encoding the
	# serialized NumPy string as a byte object
	if sys.version_info.major == 3:
		a = bytes(a, encoding="utf-8")
 
	# convert the string to a NumPy array using the supplied data
	# type and target shape
	a = np.frombuffer(base64.decodestring(a), dtype=dtype)
	a = a.reshape(shape)
 
	# return the decoded image
	return a

def prepare_image(image, target):
    # if the image mode is not RGB, convert it
    if image.mode != "RGB":
        image = image.convert("RGB")

    # resize the input image and preprocess it
    image = image.resize(target)
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = imagenet_utils.preprocess_input(image)
    return image


@app.route("/imageads/v1.0/images/overlay", methods=["POST"])
def overlay():
    data = {"success": False}
    print(flask.request.method)
 
    # ensure an image was properly uploaded to our endpoint
    if flask.request.method == "POST":
        print(flask.request.json['image'])
        print(flask.request.json['label'])
        print(flask.request.json['result'])
        overlayOp = OverlayOp(False)
        overlayOp.Operator(flask.request.json['image'],
                           flask.request.json['label'],
                           flask.request.json['result'])
        data["success"] = True
        data["result"] = flask.request.json['result']
            
    # return the data dictionary as a JSON response
    return flask.jsonify(data)


@app.errorhandler(404)
def not_found(error):
    return flask.make_response(flask.jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    # start the web server
    print("* Starting web service...")
    app.run(port=5003)

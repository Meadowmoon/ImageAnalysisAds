# -*- coding: utf-8 -*-

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

POC for Object Detection using YOLO and Keras server

@author: sophie
"""
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
from keras.applications import imagenet_utils
from keras.preprocessing.image import img_to_array
import os
import tensorflow as tf
import sys
from object_detection.utils import label_map_util

# initialize constants used to control image spatial dimensions and
# data type
IMAGE_WIDTH = 224
IMAGE_HEIGHT = 224
IMAGE_CHANS = 3
IMAGE_DTYPE = "float32"

# initialize constants used for server queuing
IMAGE_QUEUE = "image_queue"
BATCH_SIZE = 32
SERVER_SLEEP = 0.25
CLIENT_SLEEP = 0.25
IMAGE_URLS = "image_urls"
CWD_PATH = os.getcwd()
PATH_TO_CKPT = os.path.join(CWD_PATH,'frozen20k', 'frozen_inference_graph.pb')
PATH_TO_LABELS = os.path.join(CWD_PATH, 'object-detection.pbtxt')
NUM_CLASSES = 1

# initialize our Flask application, Redis server
app = flask.Flask(__name__)
db = redis.StrictRedis(host="localhost", port=6379, db=0)
model = None
detection_graph = None

'''
print("* Loading model...")
# load frozen model into memory
detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
      serialized_graph = fid.read()
      od_graph_def.ParseFromString(serialized_graph)
      tf.import_graph_def(od_graph_def, name='')

print("* Model loaded")
'''
def load_image_into_numpy_array(image):
    print(image)
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
            (im_height, im_width, 3)).astype(np.uint8)
  
def run_inference_for_single_image(image, graph):
    print("run_inference_for_single_image")
    with graph.as_default():
        with tf.Session() as sess:
            # Get handles to input and output tensors
            ops = tf.get_default_graph().get_operations()
            all_tensor_names = {output.name for op in ops for output in op.outputs}
            tensor_dict = {}
            for key in [
                'num_detections', 'detection_boxes', 'detection_scores',
                'detection_classes', 'detection_masks'
            ]:
                tensor_name = key + ':0'
                if tensor_name in all_tensor_names:
                    tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                          tensor_name)
            if 'detection_masks' in tensor_dict:
                # The following processing is only for single image
                detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
                detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
                # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
                real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
                detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
                detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
                detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                        detection_masks, detection_boxes, image.shape[0], image.shape[1])
                detection_masks_reframed = tf.cast(
                        tf.greater(detection_masks_reframed, 0.5), tf.uint8)
                # Follow the convention by adding back the batch dimension
                tensor_dict['detection_masks'] = tf.expand_dims(
                        detection_masks_reframed, 0)
            image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')
    
            # Run inference
            output_dict = sess.run(tensor_dict,
                                 feed_dict={image_tensor: np.expand_dims(image, 0)})
    
            # all outputs are float32 numpy arrays, so convert types as appropriate
            output_dict['num_detections'] = int(output_dict['num_detections'][0])
            output_dict['detection_classes'] = output_dict[
                 'detection_classes'][0].astype(np.uint8)
            output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
            output_dict['detection_scores'] = output_dict['detection_scores'][0]
            if 'detection_masks' in output_dict:
                output_dict['detection_masks'] = output_dict['detection_masks'][0]
    return output_dict


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


def classify_process():
    # load the pre-trained Keras model (here we are using a model
    # pre-trained on ImageNet and provided by Keras, but you can
    # substitute in your own networks just as easily)
    #print("* Loading model...")
    #model = ResNet50(weights="imagenet")
    
    print("* Loading model...")
    # load frozen model into memory
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
          serialized_graph = fid.read()
          od_graph_def.ParseFromString(serialized_graph)
          tf.import_graph_def(od_graph_def, name='')
    
    print("* Model loaded")
    # loading label map
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, 
                                                            use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    # continually pool for new images to classify
    while True:
        queue = db.lrange(IMAGE_QUEUE, 0, BATCH_SIZE - 1)
        image_ids = []
        batch = None
        #print('polling')

        # loop over the queue
        for q in queue:
            q = json.loads(q.decode("utf-8"))
            image = base64_decode_image(q["image"], IMAGE_DTYPE, (1, IMAGE_HEIGHT, IMAGE_WIDTH, IMAGE_CHANS))
            if batch is None:
                batch = image
            else:
                batch = np.vstack([batch, image])
            image_ids.append(q["id"])

        # check to see if we need to process the batch
        if len(image_ids) > 0:
            print("found image")
            results = []
            for (image_id, img) in zip(image_ids, batch):
                image_np = img # load_image_into_numpy_array(img)
                print("loaded image into numpy")
                # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
                #image_np_expanded = np.expand_dims(image_np, axis=0)
                # Actual detection.
                output_dict = run_inference_for_single_image(image_np, detection_graph)
                
                #detect_result = detector.detect(img)
                detected_class = output_dict['detection_classes'][0]
                #print(category_index[detected_class]['name'])
                #print("detection_classes aa: " + category_index[detected_class]['name'])
                #print("detection_scores aa: " + str(output_dict['detection_scores'][0]))
                #print(type(output_dict['detection_classes'][0]))
                
                r = {"detection_classes": category_index[detected_class]['name'],
                     "detection_scores": str(output_dict['detection_scores'][0]), 
                     "detection_box": str(output_dict['detection_boxes'][0])}
                results.extend(r)
                #print(type(output_dict))
                db.set(image_id, json.dumps(r))
                print("saved result")
            #for (imageID, resultSet) in zip(imageIDs, results):
            #    print(imageID)
            #    print("result set: ")
            #    print(resultSet)
                #output = []
                #output.append(resultSet)

                # store the output predictions in the database, using
                # the image ID as the key so we can fetch the results
            #    db.set(imageID, json.dumps(resultSet))

            # remove the set of images from our queue
            db.ltrim(IMAGE_QUEUE, len(image_ids), -1)

        time.sleep(SERVER_SLEEP)


@app.route("/predict", methods=["POST"])
def predict():
    data = {"success": False}
    print(flask.request.method)

    # ensure an image was properly uploaded to our endpoint
    if flask.request.method == "POST":
        print(flask.request.files)
        if flask.request.files.get("image"):
            print(flask.request.form)
            # read the image in PIL format and prepare it for
            # classification
            print('before read')
            image = flask.request.files["image"].read()
            image = Image.open(io.BytesIO(image))
            image = prepare_image(image, (IMAGE_WIDTH, IMAGE_HEIGHT))
            print('after read')

            # ensure our NumPy array is C-contiguous as well,
            # otherwise we won't be able to serialize it
            image = image.copy(order="C")

            # generate an ID for the classification then add the
            # classification ID + image to the queue
            k = str(uuid.uuid4())
            d = {"id": k, "image": base64_encode_image(image)}
            db.rpush(IMAGE_QUEUE, json.dumps(d))
            print("dumped image to redis")

            # keep looping until our model server returns the output
            # predictions
            while True:
                # attempt to grab the output predictions
                output = db.get(k)
                print("image id: " + k)
                print("output: " + str(output))
                # check to see if our model has classified the input
                # image
                if output is not None:
                     # add the output predictions to our data
                     # dictionary so we can return it to the client
                    output = output.decode("utf-8")
                    data["predictions"] = json.loads(output)

                    # delete the result from the database and break
                    # from the polling loop
                    db.delete(k)
                    break

                # sleep for a small amount to give the model a chance
                # to classify the input image
                time.sleep(CLIENT_SLEEP)

            # indicate that the request was a success
            data["success"] = True

    # return the data dictionary as a JSON response
    return flask.jsonify(data)


if __name__ == "__main__":
    # load the function used to classify input images in a *separate*
    # thread than the one used for main classification
    print("* Starting model service...")
    t = Thread(target=classify_process, args=())
    t.daemon = True
    t.start()

    # start the web server
    print("* Starting web service...")
    app.run()

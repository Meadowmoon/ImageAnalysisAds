from flask import Flask, flash, request, redirect, url_for, render_template, current_app
from flask_login import login_required

from app.base.models import *
from app.home import blueprint
from app import db, ALLOWED_EXTENSIONS, API_PREDICT, API_OVERLAY

import uuid
import os
import ctypes  # An included library with Python install.   
import requests
import json
import cv2

'''
curl -X POST -F image=@test.jpg http://localhost:5002/imageads/v1.0/images/predict
curl -i -H "Content-Type: application/json" -X POST -d '{"image":"cup.jpg", "label": "cup-label.jpg","result":"result.jpg"}' http://localhost:5002/imageads/v1.0/images/overlay
Windows：
curl -i -H "Content-Type: application/json" -X POST -d "{\"image\":\"cup.jpg\", \"label\": \"cup-label.jpg\",\"result\":\"result.jpg\"}" http://localhost:5002/imageads/v1.0/images/overlay

'''

##  Styles:
##  0 : OK
##  1 : OK | Cancel
##  2 : Abort | Retry | Ignore
##  3 : Yes | No | Cancel
##  4 : Yes | No
##  5 : Retry | No 
##  6 : Cancel | Try Again | Continue
def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

def calculate_coordinates(box, origin_nparray):
    height, width = origin_nparray.shape[:2]

    # [0.37396324 0.25222063 0.98457134 0.8984442 ] [top, left, bottom, right]
    values = box.replace('[','').replace(']','').split()

    x1 = int(width * float(values[1]))
    y1 = int(height * float(values[0]))
    x2 = int(width * float(values[3]))
    y2 = int(height * float(values[2]))

    return x1, y1, x2, y2

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blueprint.route('/index')
@login_required
def index():
    return render_template('image_process.html')

@blueprint.route('/upload', methods=['GET','POST'])
@login_required
def upload_Image():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'image' not in request.files:
            Mbox('Error','No file part',0)
            return redirect(request.url)
        file = request.files['image']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            Mbox('Error','No selected file',0)
            return redirect(request.url)

        # Step 1 - Rename file and save to folder
        try:
            if file and allowed_file(file.filename):
                extension = file.filename.rsplit('.', 1)[1].lower()
                new_name = str(uuid.uuid4()) + '.' + extension
                originfile_path = os.path.join(current_app.config['ORIGIN_FOLDER'], new_name)
                file.save(originfile_path)
            else:
                Mbox('Error', 'File is not a image', 0)
                return redirect(request.url)

        except:
            Mbox('Error', 'Error happens in uploading file', 0)
            return redirect(request.url)
        
        # Step 2 - Invoke API to detect object to get json
        file_json = {'image': open(originfile_path, 'rb')}
        try:
            result = requests.post(API_PREDICT, files=file_json)
            if result.status_code == 200:
                parsed_json = json.loads(result.text)
                if parsed_json['success']:
                    prediction = parsed_json['predictions']
                    object_type = prediction['detection_classes']
                    score = prediction['detection_scores']
                    box = prediction['detection_box']
            else:
                Mbox('Error', 'Object detection API returns not OK status', 0)
                return redirect("image_process")
        except:
            Mbox('Error', 'Error happens in Object detection API', 0)
            return redirect("image_process")

        # Step 3 - Create image with frame
        origin_nparray = cv2.imread(originfile_path,1)
        x1, y1, x2, y2 = calculate_coordinates(box, origin_nparray)
        img_frame = cv2.rectangle(origin_nparray, (x1,y1), (x2,y2), (0,255,0), 3)

        frame_new_name = new_name.replace(extension,'')+'_framed.'+extension
        framefile_path = os.path.join(current_app.config['FRAME_FOLDER'], frame_new_name)
        cv2.imwrite(framefile_path,img_frame)

        ## Step 4 - Get label image from object

        ## Step 5 - invoke API to do overlay

        ## Step 98 - Add records in DB, only when everything successful
        # add image file in db
        file_size = os.stat(originfile_path).st_size
        image = Image(path=originfile_path, size=file_size, type='Target')
        db.session.add(image)
        #db.session.commit()

        ## Step 99. Display original image
        ori_image = os.path.join(current_app.config['STATIC_ORIGIN_FOLDER'], new_name)
        frame_image = os.path.join(current_app.config['STATIC_FRAME_FOLDER'], frame_new_name)
        score_percent = str(float(score) * 100)+'%'
        return render_template("image_process.html", original_image = ori_image, frame_image = frame_image, object_type = object_type, score = score, score_percent = score_percent)

    return redirect(request.url)


@blueprint.route('/<template>')
@login_required
def route_template(template):
    return render_template(template + '.html')


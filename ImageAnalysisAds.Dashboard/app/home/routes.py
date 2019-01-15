from flask import Flask, flash, request, redirect, url_for, render_template, current_app
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from app.base.models import *
from app.home import blueprint
from app import db, ALLOWED_EXTENSIONS, API_PREDICT, API_OVERLAY

import uuid
import os
import ctypes  # An included library with Python install.   
import requests
import json
import cv2 # 3.4.2.50
import datetime

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

def get_label_by_object(object_type):
    label_image = Image.query.join(Mapping, Mapping.labelimage_id == Image.id) \
        .filter(Mapping.object_type == object_type) \
        .filter(Image.type == 'label') \
        .first() 
    if label_image:
        label_image_path = label_image.path
    else:
        return None
    return label_image_path

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

        start_time = datetime.datetime.now()
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
        detection_json = {'image': open(originfile_path, 'rb')}
        try:
            detection_result = requests.post(API_PREDICT, files=detection_json)
            if detection_result.status_code == 200:
                parsed_json = json.loads(detection_result.text)
                if parsed_json['success']:
                    prediction = parsed_json['predictions']
                    object_type = prediction['detection_classes']
                    score = prediction['detection_scores']
                    box = prediction['detection_box']
                    if not (object_type or score or box):
                        Mbox('Error', 'No object detected', 0)
                        return redirect("image_process")
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
        frame_new_name = new_name.replace('.'+extension,'')+'_framed.'+extension
        framefile_path = os.path.join(current_app.config['FRAME_FOLDER'], frame_new_name)
        cv2.imwrite(framefile_path,img_frame)

        ## Step 4 - Get label image from object
        label_image_path = get_label_by_object(object_type)
        if label_image_path:
            full_label_path = os.path.join(current_app.config['LABEL_FOLDER'], label_image_path)
        else:
            Mbox('Error', 'Cannot find label file for object: '+object_type, 0)
            return redirect("image_process")

        ## Step 5 - Invoke API to do overlay
        result_img_name = new_name.replace('.'+extension,'')+'_result.'+extension
        result_img_path = os.path.join(current_app.config['RESULT_FOLDER'], result_img_name)
        overlay_json = {'image': originfile_path, 'label': full_label_path, 'result': result_img_path}
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        try:
            overlay_result = requests.post(API_OVERLAY, data=json.dumps(overlay_json), headers=headers)
            if overlay_result.status_code != 200:
                Mbox('Error', 'Overlay API returns not OK status', 0)
                return redirect("image_process")
        except:
            Mbox('Error', 'Error happens in Overlay API', 0)
            return redirect("image_process")

        end_time = datetime.datetime.now()

        ## Step 98 - Add records in DB, only when everything successful
        ## Image table
        try:
            file_size = os.stat(originfile_path).st_size
            ori_img_db = Image(name=new_name, size=file_size, type='Target')
            db.session.add(ori_img_db)

            file_size = os.stat(framefile_path).st_size
            frame_img_db = Image(name=frame_new_name, size=file_size, type='Frame')
            db.session.add(frame_img_db)

            file_size = os.stat(result_img_path).st_size
            result_img_db = Image(name=result_img_name, size=file_size, type='Result')
            db.session.add(result_img_db)
            db.session.commit()
        except:
            db.session.rollback()
            Mbox('Error', 'Error happens in updating table: image', 0)
            return redirect("image_process")

        ## UserImage table
        try:
            new_img_id = Image.query.filter_by(name=new_name).first().id
            user_image = UserImage(
                new_img_id,
                current_user.id,
                file.filename,
                start_time.strftime("%Y-%m-%d %X"),
                'PC'
            )
            db.session.add(user_image)
            db.session.commit()
        except:
            db.session.rollback()
            Mbox('Error', 'Error happens in updating table: userimage', 0)
            return redirect("image_process")

        ## Activity table
            userimage_id = UserImage.query.filter_by(image_id=new_img_id).first().id
            frame_img_id = Image.query.filter_by(name=frame_new_name).first().id
            result_img_id = Image.query.filter_by(name=result_img_name).first().id
            process_time = str((end_time - start_time).seconds) + '.' + str(int((end_time - start_time).microseconds)/1000 )

        ## Step 99. Display all images in page
        ori_image_static = os.path.join(current_app.config['STATIC_ORIGIN_FOLDER'], new_name)
        frame_image_static = os.path.join(current_app.config['STATIC_FRAME_FOLDER'], frame_new_name)
        result_image_static = os.path.join(current_app.config['STATIC_RESULT_FOLDER'], result_img_name)
        score_percent = str(float(score) * 100)+'%'
        return render_template("image_process.html", original_image = ori_image_static, frame_image = frame_image_static, result_image= result_image_static \
            , object_type = object_type, score = score, score_percent = score_percent)

    return redirect(request.url)


@blueprint.route('/<template>')
@login_required
def route_template(template):
    return render_template(template + '.html')


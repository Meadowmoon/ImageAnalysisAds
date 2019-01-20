from flask import Flask, flash, request, redirect, url_for, render_template, current_app
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)
from sqlalchemy.sql import func
import sqlalchemy

from app.base.models import *
from app.home import blueprint
from app import db, ALLOWED_EXTENSIONS, API_PREDICT, API_OVERLAY

import uuid
import os
import ctypes  # An included library with Python install.   
import requests
import json
import cv2 # 3.4.2.50
from datetime import datetime, timedelta, date
from clarifai.rest import ClarifaiApp

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
        label_image_path = label_image.name
    else:
        return None
    return label_image_path

def get_count_by_daterange(start_day, tomorrow):
    date_images = UserImage.query.with_entities(UserImage.upload_datetime).filter(UserImage.upload_datetime >= start_day) \
        .filter(UserImage.upload_datetime < tomorrow).all() 

    date_images_static = {}
    date_images_htmls = []
    for date_image in date_images:
        date = date_image[0].strftime('%Y-%m-%d')
        if date in date_images_static:
            date_images_static[date] += 1
        else:
            date_images_static[date] = 1
    for key, value in date_images_static.items():
        temp = [key,value]
        date_images_htmls.append(temp)
    return date_images_htmls

def is_cup_contained(file_path):
    clarifai_key = AppConfig.query.filter_by(ConfigName = 'ClarifaiKey').first().ConfigValue
    clarifai_app = ClarifaiApp(api_key=clarifai_key)
    model = clarifai_app.public_models.general_model
    response = model.predict_by_filename(file_path)
    if response:
        if response['status']['code']==10000:
            concepts = response['outputs'][0]['data']['concepts']
            for concept in concepts:
                if (concept['name'].lower() == 'cup') or (concept['name'].lower() == 'mug') or (concept['name'].lower() == 'teacup'):
                    return True
            else:
                return False
    return False

@blueprint.route('/get_labels', methods=['GET'])
@login_required
def get_labels():
    file_list=os.listdir(current_app.config['LABEL_FOLDER'])
    for fichier in file_list[:]:
        if not(allowed_file(fichier)):
            file_list.remove(fichier)

    return json.dumps(file_list)

@blueprint.route('/post_mapping', methods=['POST'])
@login_required
def post_mapping():
    object_type = request.form.get('object_type')
    label = request.form.get('labelOptions')

    image_record = Image.query.filter_by(name=label).filter_by(type='label').first()
    mapping_record = Mapping.query.filter_by(object_type=object_type).first()
    if image_record:
        mapping_record.labelimage_id = image_record.id
        db.session.commit()
    else:
        file_path = os.path.join(current_app.config['LABEL_FOLDER'], label)
        file_size = os.stat(file_path).st_size
        image = Image(name=label, size=file_size, type='label')
        db.session.add(image)
        db.session.commit()

        image_id = Image.query.filter_by(name=label).filter_by(type='label').first().id
        mapping_record.labelimage_id = image_id
        db.session.commit()

    Mbox('Info','Mapping settings is updated',0)
    return render_template('label_mapping.html')


@blueprint.route('/image_process')
@login_required
def image_process():
    return render_template('image_process.html')

@blueprint.route('/customrange', methods=['GET'])
@login_required
def show_customrange():
    start_date = datetime.strptime(request.args.get('startDate'), '%Y-%m-%d')
    end_date = datetime.strptime(request.args.get('endDate'), '%Y-%m-%d')
    date_images_htmls = get_count_by_daterange(start_date, end_date + timedelta(days=1))
    return json.dumps(date_images_htmls)

@blueprint.route('/dashboard')
@login_required
def show_dashboard():
    # User counts
    total_users = "{:,}".format(User.query.count())

    # Image counts
    total_image_int = UserImage.query.count()
    total_images = "{:,}".format(total_image_int)

    # Avg time
    avg_time = "{:.3f}".format(db.session.query(func.avg(Activity.processtime)).scalar())

    # Detection Activities
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    start_day = today - timedelta(days=6)
    date_images_htmls = get_count_by_daterange(start_day, tomorrow)

    # top 5 objects
    object_counts = Activity.query.with_entities(Activity.object_type, func.count(Activity.object_type)) \
        .group_by(Activity.object_type).all()
    object_counts = sorted(object_counts, key=lambda x: x[1],  reverse=True)
    if len(object_counts) > 5:
        object_counts = object_counts[:5]

    objects_htmls = []
    for object_count in object_counts:
        percent = '{:.1f}'.format((object_count[1]/total_image_int) * 100) + '%'
        object_html = []
        object_html.append(object_count[0])
        object_html.append(object_count[1])
        object_html.append(percent)
        objects_htmls.append(object_html)
    
    # device usage
    device_counts = UserImage.query.with_entities(UserImage.device, func.count(UserImage.device)) \
        .group_by(UserImage.device).all()
    device_counts = sorted(device_counts, key=lambda x: x[1],  reverse=True)
    if len(device_counts) > 5:
        device_counts = device_counts[:5]

    i = 0
    device_htmls = []
    for device_count in device_counts:
        percent = str(round(device_count[1]/total_image_int * 100)) + '%'
        device_html = []
        device_html.append(device_count[0])
        device_html.append(device_count[1])
        device_html.append(percent)
        if i==0:
            device_html.append("#BDC3C7")
        if i==1:
            device_html.append("#9B59B6")
        if i==2:
            device_html.append("#E74C3C")
        if i==3:
            device_html.append("#26B99A")
        if i==4:
            device_html.append("#3498DB")
        device_htmls.append(device_html)
        i+=1
    
    # Active Users
    user_images = UserImage.query.join(User, UserImage.user_id == User.id) \
        .with_entities(User.username, func.count(User.username)) \
        .group_by(User.username).all()
    user_images = sorted(user_images, key=lambda x: x[1],  reverse=True)
    if len(user_images) > 7:
        user_images = user_images[:7]

    return render_template('dashboard.html', \
        total_users = total_users, total_images = total_images, avg_time = avg_time, date_images_htmls=date_images_htmls, \
        objects_htmls = objects_htmls, device_htmls = device_htmls, user_images = user_images)

@blueprint.route('/upload', methods=['GET','POST'])
@login_required
def upload_Image():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'image' not in request.files:
            Mbox('Error','No file part',0)
            return redirect("image_process")
        file = request.files['image']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            Mbox('Error','No selected file',0)
            return redirect("image_process")

        start_time = datetime.now()
        # Step 1 - Rename file and save to folder
        try:
            if file and allowed_file(file.filename):
                extension = file.filename.rsplit('.', 1)[1].lower()
                new_name = str(uuid.uuid4()) + '.' + extension
                originfile_path = os.path.join(current_app.config['ORIGIN_FOLDER'], new_name)
                file.save(originfile_path)
            else:
                Mbox('Error', 'File is not a image', 0)
                return redirect("image_process")

        except:
            Mbox('Error', 'Error happens in uploading file', 0)
            return redirect("image_process")
        
        # Step 2 - Invoke API to detect object to get json
        app_config_API = AppConfig.query.filter_by(ConfigName = 'ExternalObjectDetectionAPIMode').first().ConfigValue
        if app_config_API == 'Enable':
            cup_contained = is_cup_contained(originfile_path)            
            if not cup_contained:
                Mbox('Info', 'No cups detected', 0)
                return redirect("image_process")

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

        end_time = datetime.now()

        ## Step 98 - Add records in DB, only when everything successful
        ## Image table
        try:
            file_size = os.stat(originfile_path).st_size
            ori_img_db = Image(name=new_name, size=file_size, type='target')
            db.session.add(ori_img_db)

            file_size = os.stat(framefile_path).st_size
            frame_img_db = Image(name=frame_new_name, size=file_size, type='frame')
            db.session.add(frame_img_db)

            file_size = os.stat(result_img_path).st_size
            result_img_db = Image(name=result_img_name, size=file_size, type='result')
            db.session.add(result_img_db)
            db.session.commit()
        except Exception as e:
            print(str(e))
            db.session.rollback()
            Mbox('Error', 'Error happens in updating table: image', 0)
            return redirect("image_process")

        ## UserImage table
        try:
            new_img_id = Image.query.filter_by(name=new_name).first().id
            user_image = UserImage(
                image_id = new_img_id,
                user_id = current_user.id,
                origin_filename = file.filename,
                upload_datetime = start_time,
                device = 'Windows'
            )
            db.session.add(user_image)
            db.session.commit()
        except Exception as e:
            print(str(e))
            db.session.rollback()
            Mbox('Error', 'Error happens in updating table: userimage', 0)
            return redirect("image_process")

        ## Activity table
        try:
            userimage_id = UserImage.query.filter_by(image_id=new_img_id).first().id
            frame_img_id = Image.query.filter_by(name=frame_new_name).first().id
            result_img_id = Image.query.filter_by(name=result_img_name).first().id
            process_time = str((end_time - start_time).seconds) + '.' + str(int(int((end_time - start_time).microseconds)/1000))
            activity = Activity(
                userimage_id = userimage_id,
                object_type = object_type,
                score = score,
                result_json = detection_result.text,
                frameimage_id = frame_img_id,
                resultimage_id = result_img_id,
                processtime = process_time
            )
            db.session.add(activity)
            db.session.commit()
        except Exception as e:
            print(str(e))
            db.session.rollback()
            Mbox('Error', 'Error happens in updating table: activity', 0)
            return redirect("image_process")

        ## Step 99. Display all images in page
        ori_image_static = os.path.join(current_app.config['STATIC_ORIGIN_FOLDER'], new_name)
        frame_image_static = os.path.join(current_app.config['STATIC_FRAME_FOLDER'], frame_new_name)
        result_image_static = os.path.join(current_app.config['STATIC_RESULT_FOLDER'], result_img_name)
        score_percent = str(float(score) * 100)+'%'
        return render_template("image_process.html", original_image = ori_image_static, frame_image = frame_image_static, result_image= result_image_static \
            , object_type = object_type, score = '{:.2f}'.format(float(score)), json= box, score_percent = score_percent)

    return redirect("image_process")

@blueprint.route('/<template>')
@login_required
def route_template(template):
    return render_template(template + '.html')


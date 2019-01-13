from app.config import *
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from logging import basicConfig, DEBUG, getLogger, StreamHandler
import os

db = SQLAlchemy()
login_manager = LoginManager()
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
API_PREDICT = 'http://localhost:5002/imageads/v1.0/images/predict'
API_OVERLAY = 'http://localhost:5003/imageads/v1.0/images/overlay'

def register_folders(app):
    current_dir = os.getcwd()
    DB_FOLDER = current_dir+'\\db'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+DB_FOLDER+"\\database.db"

    image_folder = current_dir+'\\app\\base\\static\\images'
    app.config['ORIGIN_FOLDER'] = image_folder+'\\img_origin'
    app.config['FRAME_FOLDER'] = image_folder+'\\img_framed'
    app.config['RESULT_FOLDER'] = image_folder+'\\img_result'
    app.config['LABEL_FOLDER'] = image_folder+'\\label'

    app.config['STATIC_ORIGIN_FOLDER'] = os.path.join('\static', 'images', 'img_origin')
    app.config['STATIC_FRAME_FOLDER'] = os.path.join('\static', 'images', 'img_framed')
    app.config['STATIC_RESULT_FOLDER'] = os.path.join('\static', 'images', 'img_result')
    app.config['STATIC_LABEL_FOLDER'] = os.path.join('\static', 'images', 'label')

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app):
    for module_name in ('base', 'forms', 'ui', 'home', 'tables', 'data', 'additional'):
        module = import_module('app.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):

    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def configure_logs(app):
    basicConfig(filename='error.log', level=DEBUG)
    logger = getLogger()
    logger.addHandler(StreamHandler())


def create_app(selenium=False):
    app = Flask(__name__, static_folder='base/static')
    app.config.from_object(DebugConfig)
    if selenium:
        app.config['LOGIN_DISABLED'] = True

    register_folders(app)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    configure_logs(app)
    return app

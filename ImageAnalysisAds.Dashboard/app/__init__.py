from app.config import *
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from logging import basicConfig, DEBUG, getLogger, StreamHandler
import os

db = SQLAlchemy()
login_manager = LoginManager()
RESOURCE_FOLDER_PATH = None

def get_resources_folder():
    return os.path.dirname(os.getcwd()) + '\\resources'

def register_folders(app, resource_folder_path):
    UPLOAD_FOLDER = resource_folder_path+'\\img_origin'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    DB_FOLDER = resource_folder_path+'\\db'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+DB_FOLDER+"\\database.db"


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

    RESOURCE_FOLDER_PATH = get_resources_folder()
    register_folders(app, RESOURCE_FOLDER_PATH)

    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    configure_logs(app)
    return app

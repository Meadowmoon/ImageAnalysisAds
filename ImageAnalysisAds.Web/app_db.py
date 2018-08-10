import os
from flask_sqlalchemy import SQLAlchemy

class DBManager():

    __instance = None
    __app = None
    project_dir = os.path.dirname(os.path.abspath(__file__))
    database_file = "sqlite:///{}".format(os.path.join(project_dir, "database/database.db"))

    @staticmethod
    def getInstance(app):
        """ Static access method. """
        if DBManager.__instance == None:
            DBManager(app)
        return DBManager.__instance

    def __init__(self, app):
        """ Virtually private constructor. """
        if DBManager.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            app.config["SQLALCHEMY_DATABASE_URI"] = DBManager.database_file
            DBManager.__instance = self
            DBManager.__app = app

    def get_db_instance(self):
        return SQLAlchemy(DBManager.__app)

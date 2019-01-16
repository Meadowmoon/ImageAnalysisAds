from app import db, login_manager
from flask_login import UserMixin
from sqlalchemy import DateTime, Column, Integer, String, ForeignKey
from flask_sqlalchemy import SQLAlchemy 

class User(db.Model, UserMixin):

    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    username = Column(String(120), unique=True)
    email = Column(String(120), unique=True)
    password = Column(String(30))

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]
            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)

class Image(db.Model):

    __tablename__ = 'Image'

    id = Column(Integer, primary_key = True)
    name = Column(String(120), unique = True, nullable = False)
    size = Column(String(30), nullable = False)
    type = Column(String(10), nullable = False)

    def __repr__(self):
        return str(self.type)

class UserImage(db.Model):

    __tablename__ = 'UserImage'

    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, db.ForeignKey('Image.id'), nullable=False)
    user_id = Column(Integer, db.ForeignKey('User.id'), nullable=False)
    origin_filename = Column(String(120), nullable=False)
    upload_datetime = Column(String(20), nullable = False)
    device = Column(String(10), nullable = False)

    def __repr__(self):
        return str(self.id)

class Mapping(db.Model):

    __tablename__ = 'Mapping'

    id = Column(Integer, primary_key=True)
    object_type = Column(String(30), nullable=False)
    labelimage_id = Column(Integer, db.ForeignKey('Image.id'), nullable=False)

    def __repr__(self):
        return str(self.object_type)

class Activity(db.Model):

    __tablename__ = 'Activity'

    id = Column(Integer, primary_key=True)
    userimage_id = Column(Integer, db.ForeignKey('UserImage.id'), nullable=False)
    object_type = Column(String(30), nullable = False)
    score = Column(String(10), nullable = False)
    result_json = Column(String(1024), nullable = False)
    frameimage_id = Column(Integer, db.ForeignKey('Image.id'), nullable=False)
    resultimage_id = Column(Integer, db.ForeignKey('Image.id'), nullable=False)
    processtime = Column(String(10), nullable = False)

    def __repr__(self):
        return str(self.id)

@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    return user if user else None




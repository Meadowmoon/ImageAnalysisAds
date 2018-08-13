import flask_login

from flask import Flask, render_template, request, redirect
from flask_login import LoginManager
from app_logger import Logger
from app_database import db_session, init_db
from app_models import User

logger = None

# Initialize session manager
login_manager = LoginManager()

app = Flask(__name__)
login_manager.init_app(app)

@app.route('/')
@app.route('/main')
def main():
    return render_template('index.html')

@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')

@app.route('/signup', methods = ['POST'])
def signup():
    name = request.form['inputName']
    email = request.form['inputEmail']
    password = request.form['inputPassword']

    user = User(name, email, password)
    db_session.add(user)
    db_session.commit()

    print(f'User name is {name}, email is {email}, password is {password}')
    return redirect('/')

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == '__main__':
    logger = Logger().get_logger(__name__)
    init_db()
    app.run()
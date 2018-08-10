import flask_login
from flask import Flask, render_template, request, redirect
from flask_login import LoginManager
from app_logger import Logger

logger = ''

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

    print(f'User name is {name}, email is {email}, password is {password}')
    return redirect('/')

if __name__ == '__main__':
    logger = Logger().get_logger(__name__)
    app.run()
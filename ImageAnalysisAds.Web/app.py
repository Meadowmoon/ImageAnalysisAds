from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route("/")
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
    app.run()
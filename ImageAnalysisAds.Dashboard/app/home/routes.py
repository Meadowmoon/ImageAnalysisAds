from app.home import blueprint
from flask import render_template
from flask_login import login_required


@blueprint.route('/index')
@login_required
def index():
    return render_template('image_process.html')

@blueprint.route('/upload', methods=['GET','POST'])
@login_required
def uploadImage(request):
    file = request.files['image']
    print(file)

@blueprint.route('/<template>')
@login_required
def route_template(template):
    return render_template(template + '.html')


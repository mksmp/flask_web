from flask import Flask, render_template

app = Flask(__name__)
application = app

app.config.from_pyfile('config.py')

from auth import bp as auth_bp, init_login_manager
app.register_blueprint(auth_bp)

init_login_manager(app)

@app.route('/')
def index():
    categories = []
    return render_template(
        'index.html', 
        categories=categories,
    )

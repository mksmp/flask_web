from urllib import request
from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к этой странице необходимо пройти процедуру аутентифкации.'
login_manager.login_message_category = 'warning'

app = Flask(__name__)
application = app

login_manager.init_app(app) # доступ логину ко входу в систему

class User(UserMixin): # usermixin для упрощения реализации класса user. По умолчанию реализует все стандартные поля
    def __init__(self, user_id, login, password):
        super().__init__() # при помощи super вызывается родительский метод и дополняется своим методом. 
        # super.init вызывает инициализацию родительского класса
        self.id = user_id
        self.login = login
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    for user in get_users():
        if user['user_id'] == user_id:
            return User(**user)
    return None 


app.config.from_pyfile('config.py')

def get_users():
    return [{'user_id': '1', 'login': 'user', 'password': 'qwerty'}]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/visits')
def visits():
    if session.get('visits_count') is None:
        session['visits_count'] = 1
    else:
        session['visits_count'] += 1
    return render_template('visits.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == "POST":
        login_ = request.form.get('login')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        for user in get_users():
            if user['login'] == login_ and user['password'] == password:
                login_user(User(**user), remember=remember_me)
                flash('Вы успешно прошли процедуру аутентификации.', 'success') # уведомление об успешном проходе
                next_ = request.args.get('next') # если не использовать next, то наше приложение будет отрыто для перенаправлений
                return redirect(next_ or url_for('index'))
        flash('Введены неверные логин и/или пароль.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user() # выход из учетки и редирект на главную
    return redirect(url_for('index'))


@app.route('/secret_page')
@login_required # если пользователь не авторизирован, то выдаст ошибку, что мы не авторизированы - 401
def secret_page():
    return render_template('secret_page.html')
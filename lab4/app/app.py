from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin,  login_user, logout_user, login_required
from mysql_db import MySQL
import mysql.connector as connector
import re
import hashlib

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа к данной странице необходимо пройти процедуру аутентификации'
login_manager.login_message_category = 'warning'

app = Flask(__name__)
application = app

login_manager.init_app(app)

app.config.from_pyfile('config.py')

mysql = MySQL(app)

CREATE_PARAMS = ['login', 'password', 'first_name',
                 'last_name', 'middle_name', 'role_id']
UPDATE_PARAMS = ['first_name', 'last_name', 'middle_name', 'role_id']
CHANGE_PASS_PARAMS = ['old_pass', 'new_pass', 'r_new_pass']


def request_params(params_list):
    params = {}
    for param_name in params_list:
        params[param_name] = request.form.get(param_name) or None
    return params


def load_roles():
    with mysql.connection.cursor(named_tuple=True) as cursor:
        cursor.execute('SELECT id, name FROM roles;')
        roles = cursor.fetchall()
    return roles


class User(UserMixin):
    def __init__(self, user_id, login):
        super().__init__()
        self.id = user_id
        self.login = login


@login_manager.user_loader
def load_user(user_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        cursor.execute('SELECT * FROM users WHERE id=%s;', (user_id,))
        db_user = cursor.fetchone()
    if db_user:
        return User(user_id=db_user.id, login=db_user.login)
    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_ = request.form.get('login')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == "on"
        with mysql.connection.cursor(named_tuple=True) as cursor:
            cursor.execute(
                'SELECT * FROM users WHERE login=%s AND password_hash=SHA2(%s, 256);', (login_, password))
            db_user = cursor.fetchone()
        if db_user:
            login_user(User(user_id=db_user.id, login=db_user.login),
                       remember=remember_me)
            flash('Вы успешно прошли процедуру аутентификации.', 'success')
            next_ = request.args.get('next')
            return redirect(next_ or url_for('index'))
        flash('Введены неверные логин и/или пароль.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/users')
def users():
    with mysql.connection.cursor(named_tuple=True) as cursor:
        cursor.execute(
            'SELECT users.*, roles.name AS role_name FROM users LEFT JOIN roles ON users.role_id = roles.id;')
        users = cursor.fetchall()
    return render_template('users/index.html', users=users)


def check_login(login):
    if login == None:
        return 'Поле не может быть пустым'
    elif not check_login_req(login):
        return 'Логин не соответствует требованиям'
    return ''


def check_login_req(login):
    if (not re.search(r'[^a-zA-Z1-9]', login)) and len(login) >= 5:
        return True
    else:
        return False


def check_pass(passw):
    err_msg = ''
    if passw == None:
        return 'Поле не может быть пустым'
    check_pass_eq = 0
    if not check_pass_len(passw):
        check_pass_eq = check_pass_eq + 1
    if not check_pass_oneletter(passw):
        check_pass_eq = check_pass_eq + 1
    # if not check_pass_latkir_arabdigit(passw):
    #     check_pass_eq = check_pass_eq + 1
    if not check_pass_digit(passw):
        check_pass_eq = check_pass_eq + 1
    if not check_pass_specsymb(passw):
        check_pass_eq = check_pass_eq + 1
    if ' ' in passw:
        check_pass_eq = check_pass_eq + 1
    if check_pass_eq != 0:
        return 'Пароль не соответствует требованиям'
    return err_msg


def check_pass_len(passw):
    if len(passw) >= 8 and len(passw) <= 128:
        return True
    else:
        return False


def check_pass_oneletter(passw):
    if passw.lower() != passw and passw.upper() != passw:
        return True
    else:
        return False


def check_pass_latkir_arabdigit(passw):
    if re.search(r'[^a-zA-Zа-яА-Я1-9]', passw):
        return True
    else:
        return False


def check_pass_digit(passw):
    if any(char.isdigit() for char in passw):
        return True
    else:
        return False


def check_pass_specsymb(passw):
    check_str = '~!?@#$%^&*_-+()[]{}></\|\"\'.,:;'
    for i in passw:
        if not check_pass_latkir_arabdigit(i) or i in check_str:
            return True
        else:
            return False
    

def check_last(passw):
    if passw == None:
        return 'Поле не может быть пустым'
    return ''


def check_first(passw):
    if passw == None:
        return 'Поле не может быть пустым'
    return ''


def check_middle(passw):
    if passw == None:
        return 'Поле не может быть пустым'
    return ''


def check_nulls(arr):
    for i in arr:
        if i != '':
            return False
    return True


@app.route('/users/new')
@login_required
def new():
    return render_template('users/new.html', user={}, roles=load_roles(), err_msg=['', '', '', '', ''])


@app.route('/users/create', methods=['POST'])
@login_required
def create():
    params = request_params(CREATE_PARAMS)

    params['role_id'] = int(params['role_id']) if params['role_id'] else None

    err_msg = ['' for i in range(len(params) - 1)]

    err_msg[0] = check_login(params['login'])
    err_msg[1] = check_pass(params['password'])
    err_msg[2] = check_last(params['last_name'])
    err_msg[3] = check_first(params['first_name'])
    err_msg[4] = check_middle(params['middle_name'])

    err_check = check_nulls(err_msg)

    if err_check == False:
        return render_template('users/new.html', user=params, roles=load_roles(), err_msg=err_msg)

    with mysql.connection.cursor(named_tuple=True) as cursor:
        try:
            cursor.execute(
                ('INSERT INTO users (login, password_hash, last_name, first_name, middle_name, role_id)'
                 'VALUES (%(login)s, SHA2(%(password)s, 256), %(last_name)s, %(first_name)s, %(middle_name)s, %(role_id)s);'),
                params
            )
            mysql.connection.commit()
        except connector.Error:
            flash('Введены некорректные данные. Ошибка сохранения', 'danger')
            return render_template('users/new.html', user=params, roles=load_roles(), err_msg=err_msg)
    flash(f"Пользлватель {params.get('login')} был успешно создан", 'success')
    return redirect(url_for('users'))


@app.route('/users/<int:user_id>')
def show(user_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        cursor.execute('SELECT * FROM users WHERE id=%s;', (user_id,))
        user = cursor.fetchone()
    return render_template('users/show.html', user=user)


@app.route('/users/<int:user_id>/edit')
@login_required
def edit(user_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        cursor.execute('SELECT * FROM users WHERE id=%s;', (user_id,))
        user = cursor.fetchone()
    return render_template('users/edit.html', user=user, roles=load_roles(), err_msg=['', '', '', '', ''])


@app.route('/users/<int:user_id>/update', methods=['POST'])
@login_required
def update(user_id):
    params = request_params(UPDATE_PARAMS)
    params['role_id'] = int(params['role_id']) if params['role_id'] else None
    params['id'] = user_id
    with mysql.connection.cursor(named_tuple=True) as cursor:
        try:
            cursor.execute(
                ('UPDATE users SET last_name=%(last_name)s, first_name=%(first_name)s, '
                 'middle_name=%(middle_name)s, role_id=%(role_id)s WHERE id = %(id)s;'), params)
            mysql.connection.commit()
        except connector.Error:
            flash('Введены некорректные данные. Ошибка сохранения', 'danger')
            return render_template('users/edit.html', user=params, roles=load_roles())
    flash("Пользователь был успешно обновлён!", 'success')
    return redirect(url_for('show', user_id=user_id))


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete(user_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        try:
            cursor.execute('DELETE FROM users WHERE id=%s;', (user_id,))
            mysql.connection.commit()
        except connector.Error:
            flash('Не удалось удалить пользователя', 'danger')
            return redirect(url_for('users'))
    flash("Пользователь был успешно удалён!", 'success')
    return redirect(url_for('users'))


@app.route('/users/<int:user_id>/new_pass')
@login_required
def new_pass(user_id):
    # with mysql.connection.cursor(named_tuple=True) as cursor:
    #     cursor.execute('SELECT * FROM users WHERE id=%s;', (user_id,))
    #     user = cursor.fetchone()
    return render_template('users/newpass.html', err_msg=['', '', ''], user_id=user_id, user_pass={})



@app.route('/users/<int:user_id>/change_pass', methods=['POST'])
@login_required
def change_pass(user_id):
    params = request_params(CHANGE_PASS_PARAMS)
    # params['id'] = user_id

    err_msg = ['' for i in range(len(params))]

    if params['old_pass'] == None:
        err_msg[0] = 'Поле не может быть пустым'
    if params['new_pass'] == None:
        err_msg[1] = 'Поле не может быть пустым'
    # err_msg[1] = check_pass(params['new_pass'])
    if params['r_new_pass'] == None:
        err_msg[2] = 'Поле не может быть пустым'
    
    err_check = check_nulls(err_msg)
    if err_check == False:
        return render_template('users/newpass.html', user_pass=params, err_msg=err_msg, user_id=user_id)

    with mysql.connection.cursor(named_tuple=True) as cursor:
        cursor.execute('SELECT password_hash FROM users WHERE id=%s;', (user_id,))
        old_pass = cursor.fetchone()

    old_pass_h = hashlib.new('sha256')
    old_pass_h.update(params['old_pass'].encode('utf-8'))

    if old_pass_h.hexdigest() != old_pass.password_hash:
        err_msg[0] = 'Пароль не совпадает со старым'
    err_msg[1] = check_pass(params['new_pass'])
    if params['new_pass'] != params['r_new_pass']:
        err_msg[2] = 'Пароли не совпадают'
    
    err_check = check_nulls(err_msg)
    if err_check == False:
        return render_template('users/newpass.html', user_pass=params, err_msg=err_msg, user_id=user_id)
    
    params['id'] = user_id

    with mysql.connection.cursor(named_tuple=True) as cursor:
        try:
            cursor.execute(
                ('UPDATE users SET password_hash=SHA2(%(new_pass)s, 256) WHERE id = %(id)s;'), params)
            mysql.connection.commit()
        except connector.Error:
            flash('Ошибка сохранения', 'danger')
            return render_template('users/newpass.html', user_pass=params, err_msg=err_msg, user_id=user_id)

    flash('Пароль успешно изменен.', 'success')
    return redirect(url_for('index'))
from flask import Flask, render_template, request, make_response
import operator as op
import string

app = Flask(__name__)
application = app

OPERATIONS = { '+' : op.add, '-' : op.sub, '*' : op.mul, '/' : op.truediv }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/args')
def args():
    return render_template('args.html')


@app.route('/check_tel', methods=['GET', 'POST'])
def check_tel():
    check_string = ' ()-.+'
    result = ''
    count = 0
    check = True
    err_msg_symbols = ''
    err_msg_volume = ''
    if request.method == 'POST':
        for i in request.form.get('telephone'):
            if i in string.digits:
                count = count + 1
                result = result + i
            elif i in check_string:
                pass
            else:
                check = False
                err_msg_symbols = 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'
        if count == 11 and (request.form.get('telephone').startswith('8') or request.form.get('telephone').startswith('+7')) and check:
            pass
        
        elif count == 10 and not(request.form.get('telephone').startswith('8') and request.form.get('telephone').startswith('+7')) and check:
            result = '8' + result
        elif count != 11 and count != 10:
            check = False
            err_msg_volume = 'Недопустимый ввод. Неверное количество цифр.'
        
        result = '8-' + result[1:4] + '-' + result[4:7] + '-' + result[7:9] + '-' + result[9:11]
    return render_template('check_tel.html', err_msg_symbols=err_msg_symbols, err_msg_volume=err_msg_volume, check=check, result=result)



@app.route('/calc', methods=['GET', 'POST'])
def calc():
    result = None
    error_msg = None
    if request.method == 'POST':
        try:
            operand1 = float(request.form.get('operand1'))
            operand2 = float(request.form.get('operand2'))
            operation = request.form.get('operation')
            result = OPERATIONS[operation](operand1, operand2)
        except ValueError:
            error_msg = 'Нужно вводить только цифры.'
        except ZeroDivisionError:
            error_msg = 'На ноль делить нельзя.'
    return render_template('calc.html', operations=OPERATIONS, result=result, error_msg=error_msg)


@app.route('/form', methods=['GET', 'POST'])
def form():
    return render_template('form.html')


@app.route('/headers')
def headers():
    url = request.url
    return render_template('headers.html')


@app.route('/cookies')
def cookies():
    response = make_response(render_template('cookies.html'))
    if request.cookies.get('name') is None:
        response.set_cookie('name', 'qq')
    else:
        response.set_cookie('name', 'qq', expires=0)
    return response
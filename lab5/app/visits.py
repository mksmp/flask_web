from flask import Flask, render_template, session, request, redirect, url_for, flash, Blueprint, send_file
from flask_login import current_user
from app import mysql
import math
import io
import datetime

bp = Blueprint('visits', __name__, url_prefix='/visits')

PER_PAGE = 10

def convert_to_csv(records):
    fields = records[0]._fields
    result = 'No,' + ','.join(fields) + '\n'
    for i, record in enumerate(records):
        result += f'{i+1},' + ','.join([str(getattr(record, f, '')) for f in fields]) + '\n'

    return result


def generate_report(records):
    buffer = io.BytesIO()
    buffer.write(convert_to_csv(records).encode(encoding='utf-8'))
    buffer.seek(0)

    return buffer


@bp.route('/logs')
def logs():
    page = request.args.get('page', 1, type=int)

    if current_user.can("watch_stat"):
        query = ('SELECT visit_logs.*, users.last_name, users.first_name, users.middle_name' 
            ' FROM visit_logs LEFT JOIN users ON visit_logs.user_id = users.id' 
            ' ORDER BY visit_logs.created_at DESC' 
            ' LIMIT %s'
            ' OFFSET %s;')
        query_params = (PER_PAGE, PER_PAGE*(page-1))

        count_query = ('SELECT COUNT(*) AS count from visit_logs;')
        count_query_params = ()
        
    else:
        query = ('SELECT visit_logs.*, users.last_name, users.first_name, users.middle_name' 
            ' FROM visit_logs LEFT JOIN users ON visit_logs.user_id = users.id WHERE users.id = %s' 
            ' ORDER BY visit_logs.created_at DESC' 
            ' LIMIT %s'
            ' OFFSET %s;')
        query_params = (current_user.id, PER_PAGE, PER_PAGE*(page-1))

        count_query = ('SELECT COUNT(*) AS count from visit_logs WHERE user_id = %s;')
        count_query_params = (current_user.id, )
        

    with mysql.connection.cursor(named_tuple=True) as cursor:
        cursor.execute(query, query_params)
        records = cursor.fetchall()

    with mysql.connection.cursor(named_tuple=True) as cursor:
        cursor.execute(count_query, count_query_params)   
        total_count = cursor.fetchone().count

    total_pages = math.ceil(total_count/PER_PAGE)

    return render_template('visits/logs.html', records=records, page=page, total_pages=total_pages)


@bp.route('/stats/users')
def users_stat():
    query = ('SELECT users.last_name, users.first_name, users.middle_name, COUNT(*) AS count'
            ' FROM users RIGHT JOIN visit_logs ON visit_logs.user_id = users.id' 
            ' GROUP BY visit_logs.user_id' 
            ' ORDER BY count DESC;')

    with mysql.connection.cursor(named_tuple=True) as cursor:
        cursor.execute(query)
        records = cursor.fetchall()

    if request.args.get('download_csv'):
        f = generate_report(records)
        filename = datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '_users_stat.csv'
        return send_file(f, mimetype='text/csv', as_attachment=True, attachment_filename=filename)

    return render_template('visits/users_stat.html', records=records)


@bp.route('/stats/pages')
def pages_stat():
    query = ('SELECT DISTINCT(path), COUNT(*) as count' 
            ' FROM visit_logs' 
            ' GROUP BY path'
            ' ORDER BY count DESC;')

    with mysql.connection.cursor(named_tuple=True) as cursor:
        cursor.execute(query)
        records = cursor.fetchall()

    if request.args.get('download_csv'):
        f = generate_report(records)
        filename = datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '_pages_stat.csv'
        return send_file(f, mimetype='text/csv', as_attachment=True, attachment_filename=filename)
    
    return render_template('visits/pages_stat.html', records=records)
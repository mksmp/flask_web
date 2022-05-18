from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import mysql


bp = Blueprint('visits', __name__, url_prefix='/visits')

@bp.route('/logs')
def logs():
    with mysql.connection.cursor(named_tuple=True) as cursor:
        cursor.execute('SELECT * FROM visit_logs LEFT JOIN users ON visit_logs.user_id = users.id ORDER BY created_at DESC;')
        records = cursor.fetchall()
    return render_template('visits/logs.html', records=records)
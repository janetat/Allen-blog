from app.main import main
from flask import render_template

@main.route('/')
@main.route('/index')
def index():
    return 'Hello Allen!'

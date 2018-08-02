from flask import render_template
from . import errors
from app import db


@errors.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@errors.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500
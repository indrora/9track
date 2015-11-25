# -*- coding: utf-8 -*-
__version__ = '0.1'
from flask import Flask
from flask import Request
import bcrypt
app = Flask('project')
app.config.from_object('project.config')
app.secret_key = 'dxTsvQQVc6SF8yTJITQVA.'


class SessionAwareRequest(Request):
    """
        A request class that is aware of the currently logged in user.
        This allows us to use <request.user> in templates?
    """

    user = None

    def __init__(self, environ, populate_request=True, shallow=False):
        super(SessionAwareRequest, self).__init__(environ, populate_request, shallow)

@app.before_request
def request_add_userdata():
    """ Called before the request to add userdata for the current session. """
    request.user = User.get_current()

app.request_class = SessionAwareRequest

# Initialize the database
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

from project.controllers import *

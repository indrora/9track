from project import app
from project import db
from project.models import User
from project.models import Root
from project.models import FilesystemObject
from project.preview import get_previews
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask import abort
from flask import send_file
import os


###################################################################################################
# Functions for handling most of the parts.

@app.route("/")
def index():
    if User.get_current() is not None:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route("/login", methods=['POST', 'GET'] )
def login():
    if User.get_current() is not None:
        return redirect(url_for('index'))
    if request.method == 'POST':
        # Check the username given
        if not 'username' in request.form or not 'password' in request.form:
            abort(400)
        u_username = request.form['username']
        u_password = request.form['password']
        if User.login(u_username, u_password) is None:
            app.logger.error("Failed login for %s", u_username)
            return render_template("login.html", error = "Invalid credentials")
        app.logger.info("Logged in as %s", u_username)
        return redirect(url_for('index'))
    else:
        return render_template("login.html")

@app.route('/logout')
def logout():
    app.logger.debug("Logged out user %s", User.get_current())
    User.logout()
    return redirect('/login')

###################################################################################################
# Functions for handling libraries

@app.route("/r:<root_id>")
def root_explore(root_id):
    # Can the current user see the specified root?
    root = Root.query.get(root_id)
    if root is None:
        abort(404)
    if(root.visibility == 'private' and root.owner.id != request.user.id):
        return redirect(url_for('login'))
    
    objects = FilesystemObject.query.filter_by(root_uuid=root.id, path="").all()
    if request.user is None:
        # view only public files
         objects = filter( lambda x: x.get_visibility() == 'public', list(objects) )
    return render_template('object_listing.html', title=root.name, root=root, listing_objects=objects)

@app.route("/r:<root_id>/rescan")
def root_rescan(root_id):
    root = Root.query.get(root_id)
    return redirect(url_for('index'))

@app.route("/o:<object_id>")
def view_object(object_id):
    # get the object in question
    obj_view = FilesystemObject.query.filter_by(id=object_id).one_or_none()
    if obj_view is None:
        abort(404)
    elif request.user is None and obj_view.get_visibility() == 'private':
        return redirect(url_for('login'))
    elif request.user is not None and request.user.id != obj_view.root.owner.id and obj_view.get_visibility() == 'private':
        abort(403)
    if obj_view.type == 'file':
        previews = get_previews(obj_view)
        if len(previews) > 0:
            return render_template('preview_panel.html', object=obj_view, previews=previews)
        else:
            return render_template('preview_panel.html', object=obj_view)
    else:
        children = FilesystemObject.query.filter_by(
            root_uuid=obj_view.root.id,
            path=os.path.join(obj_view.path, obj_view.filename)
            ).all()
        if request.user is None and obj_view.get_visibility() == 'protected':
            # edge case: don't show anything private if there's a protected view here.
            children = filter(lambda x: x.get_visibility() != 'private', list(children))
        if request.user is None and obj_view.get_visibility() == 'public':
            # get only public objects.
            children = filter(lambda x: x.get_visibility() =='public', list(children))
        return render_template('object_listing.html', title=obj_view.filename, root=obj_view.root, view_object=obj_view, listing_objects=children)
    abort(503)

@app.route("/o:<object_id>/<action>")
def get_object_contents(object_id,action="raw"):
    obj_view = FilesystemObject.query.filter_by(id=object_id).one_or_none()
    if obj_view is None:
        abort(404)
    elif request.user is not None and request.user.id != obj_view.root.owner.id and obj_view.get_visibility() == 'private':
        abort(403)
    dl = action=="dl"
    return send_file(obj_view.get_real_path(), attachment_filename=obj_view.filename, as_attachment=dl)

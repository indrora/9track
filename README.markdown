# 9track - A tracking document store.

9track is a lightweight document tracking store.

## Install

    virtualenv --python python2.7 9track_venv
    cd 9track venv
    git clone https://github.com/indrora/9track/ src
    pip install -r src/requirements.txt --no-index --find-links file:///tmp/packages

Update configuration in `src/project/config/__init__.py to specify database location.

## Run

    python runserver.py


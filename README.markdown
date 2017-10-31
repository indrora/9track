# 9track - A tracking document store.
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Findrora%2F9track.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2Findrora%2F9track?ref=badge_shield)


9track is a lightweight document tracking store.

## Install

    virtualenv --python python2.7 9track_venv
    cd 9track venv
    git clone https://github.com/indrora/9track/ src
    pip install -r src/requirements.txt --no-index --find-links file:///tmp/packages

Update configuration in `src/project/config/__init__.py to specify database location.

## Run

    python runserver.py



## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Findrora%2F9track.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2Findrora%2F9track?ref=badge_large)
kolibri2zim
=============

[![CodeFactor](https://www.codefactor.io/repository/github/openzim/kolibri2zim/badge)](https://www.codefactor.io/repository/github/openzim/kolibri2zim)
[![Docker](https://img.shields.io/docker/v/openzim/kolibr?label=docker&sort=semver)](https://hub.docker.com/r/openzim/kolibri)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI version shields.io](https://img.shields.io/pypi/v/kolibri2zim.svg)](https://pypi.org/project/kolibri2zim/)

`kolibr2zim` allows you to create a [ZIM file](https://openzim.org) from a Kolibri Channel.

It downloads the video (`webm` or `mp4` extension – optionnaly
recompress them in lower-quality, smaller size), the thumbnails, the
subtitles and the authors' profile pictures ; then, it create a static
HTML files folder of it before creating a ZIM off of it.

Requirements
------------

* [`ffmpeg`](https://ffmpeg.org/) for video transcoding (only used with `--use-webm` or `--low-quality`).
* `curl` and `unzip` to install Javascript dependencies. See `get_js_deps.sh` if you want to do it manually.

Installation
------------

## Virtualenv

`kolibri2zim` is a Python3 software. If you are not using the 
[Docker](https://docker.com) image, you are advised to use it in a
virtual environment to avoid installing software dependencies on your system.

```bash
python3 -m venv env      # Create virtualenv
source env/bin/Activate  # Activate the virtualenv
pip3 install kolibri2zim # Install dependencies
kolibri2zim --help       # Display kolibri2zim help
```

Call `deactivate` to quit the virtual environment.

See `requirements.txt` for the list of python dependencies.

## Docker

```bash
docker run -v my_dir:/output openzim/kolibri2zim kolibri2zim --help
```

Usage
-----

`kolibri2zim` works off a `channel-id` that you must provide. This is a 32-characters long ID that you can find in the URL of the channel you want, either from [Kolibri Studio](https://studio.learningequality.org) or the [Kolibri Catalog](https://kolibri-catalog-en.learningequality.org)

Development
-----------

Before contributing be sure to check out the
[CONTRIBUTING.md](CONTRIBUTING.md) guidelines.

License
-------

[GPLv3](https://www.gnu.org/licenses/gpl-3.0) or later, see
[LICENSE](LICENSE) for more details.

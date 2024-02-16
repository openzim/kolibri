kolibri2zim
=============

[![CodeFactor](https://www.codefactor.io/repository/github/openzim/kolibri/badge)](https://www.codefactor.io/repository/github/openzim/kolibri)
[![Docker](https://ghcr-badge.deta.dev/openzim/kolibri/latest_tag?label=docker)](https://ghcr.io/openzim/kolibri)
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
docker run -v my_dir:/output ghcr.io/openzim/kolibri2zim kolibri2zim --help
```

Usage
-----

`kolibri2zim` works off a `channel-id` that you must provide. This is a 32-characters long ID that you can find in the URL of the channel you want, either from [Kolibri Studio](https://studio.learningequality.org) or the [Kolibri Catalog](https://kolibri-catalog-en.learningequality.org)

Development
-----------

kolibri2zim adheres to openZIM's [Contribution Guidelines](https://github.com/openzim/overview/wiki/Contributing).

kolibri2zim has implemented openZIM's [Python bootstrap, conventions and policies](https://github.com/openzim/_python-bootstrap/docs/Policy.md) **v1.0.0**.

Before contributing be sure to check out the
[CONTRIBUTING.md](CONTRIBUTING.md) guidelines.

To test epubs and pdfs rendering, a potential usefull command is:
```bash
kolibri2zim --name "Biblioteca Elejandria" --output /output --tmp-dir /tmp --zim-file Biblioteca_Elejandria.zim --channel-id "fed29d60e4d84a1e8dcfc781d920b40e" --node-ids 'd92c07655128458f8248416154b18a68,89fe2f86ee3f4fbaa7fb2bf9bd56d088,75f99e6b97d14b14a4e74762ad77391f,89fe2f86ee3f4fbaa7fb2bf9bd56d088'
```

License
-------

[GPLv3](https://www.gnu.org/licenses/gpl-3.0) or later, see
[LICENSE](LICENSE) for more details.

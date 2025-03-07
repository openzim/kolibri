kolibri2zim
=============

[![CodeFactor](https://www.codefactor.io/repository/github/openzim/kolibri/badge)](https://www.codefactor.io/repository/github/openzim/kolibri)
[![Docker](https://ghcr-badge.epgl.dev/openzim/kolibri/latest_tag?label=docker)](https://ghcr.io/openzim/kolibri)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI version shields.io](https://img.shields.io/pypi/v/kolibri2zim.svg)](https://pypi.org/project/kolibri2zim/)

`kolibr2zim` allows you to create a [ZIM file](https://openzim.org) from a Kolibri Channel.

It downloads the video (`webm` or `mp4` extension – optionally
recompress them in lower-quality, smaller size), the thumbnails, the
subtitles and the authors' profile pictures ; then, it create a static
HTML files folder of it before creating a ZIM off of it.

> [!WARNING]
> This scraper is under heavy modifications to prepare a v2 including a brand new UI for navigating the tree of content and a move to Vue.JS. These changes
are already merged into `main` branch but not yet completed. Should you be interested in a stable version, please used published versions (PyPI or Docker).
We also have a `v1` branch for any urgent patch needed to current production version.

Requirements
------------

* Node 20.x
* Python 3.11
* [`ffmpeg`](https://ffmpeg.org/) for video transcoding (only used with `--use-webm` or `--low-quality`).
* `curl` and `unzip` to install Javascript dependencies. See `get_web_deps.sh` if you want to do it manually.

Installation
------------

### Virtualenv

`kolibri2zim` is a Python3 software. If you are not using the
[Docker](https://docker.com) image, you are advised to use it in a
virtual environment to avoid installing software dependencies on your system.

```bash
python3 -m venv env      # Create virtualenv
source env/bin/Activate  # Activate the virtualenv ('env/Scripts/Activate' in Windows)
pip3 install kolibri2zim # Install dependencies
kolibri2zim --help       # Display kolibri2zim help
```

Call `deactivate` to quit the virtual environment.

See `pyproject.toml` for the list of python dependencies.

To test epubs and pdfs rendering, a potential usefull command is:

```bash
kolibri2zim --name "Biblioteca Elejandria" --output /output --tmp-dir /tmp --zim-file Biblioteca_Elejandria.zim --channel-id "fed29d60e4d84a1e8dcfc781d920b40e" --node-ids 'd92c07655128458f8248416154b18a68,89fe2f86ee3f4fbaa7fb2bf9bd56d088,75f99e6b97d14b14a4e74762ad77391f,89fe2f86ee3f4fbaa7fb2bf9bd56d088'
```

### Docker

```bash
docker run -v my_dir:/output ghcr.io/openzim/kolibri kolibri2zim --help
```

Usage
-----

`kolibri2zim` works off a `channel-id` that you must provide. This is a 32-characters long ID that you can find in the URL of the channel you want, either from [Kolibri Studio](https://studio.learningequality.org) or the [Kolibri Catalog](https://kolibri-catalog-en.learningequality.org)

Development
-----------

kolibri2zim adheres to openZIM's [Contribution Guidelines](https://github.com/openzim/overview/wiki/Contributing).

kolibri2zim has implemented openZIM's [Python bootstrap, conventions and policies](https://github.com/openzim/_python-bootstrap/blob/main/docs/Policy.md) **v1.0.0**.

Before contributing be sure to check out the
[CONTRIBUTING.md](CONTRIBUTING.md) guidelines.

Some usefull test channels:

- 7f744ce8d28b471eaf663abd60c92267: a very minimal channel with all kind of content
- 9f15f4e9aeaa48b5ae271e5749d6fe80 : a small channel with significantly nested items and all kind of content

### Build and running scraper locally

You have to:

- build the `zimui` frontend which will be embededed inside the ZIM (and redo it every time you make modifications to the `zimui`)
- run the `scraper` to retrieve FCC curriculum and build the ZIM

Sample commands:

```
cd zimui
yarn install
yarn build
cd ../scraper
hatch run kolibri2zim --name "Biblioteca Elejandria" --output output --zim-file Biblioteca_Elejandria.zim --channel-id "fed29d60e4d84a1e8dcfc781d920b40e" --node-ids 'd92c07655128458f8248416154b18a68,89fe2f86ee3f4fbaa7fb2bf9bd56d088,75f99e6b97d14b14a4e74762ad77391f,89fe2f86ee3f4fbaa7fb2bf9bd56d088'
```

### Running scraper with Docker

Run from official version (published on GHCR.io) ; ZIM will be available in the `output` sub-folder of current working directory.

```
docker run --rm -it -v $(pwd)/output:/output ghcr.io/openzim/kolibri:latest kolibri2zim --name "Biblioteca Elejandria" --output /output --tmp-dir /tmp --zim-file Biblioteca_Elejandria.zim --channel-id "fed29d60e4d84a1e8dcfc781d920b40e" --node-ids 'd92c07655128458f8248416154b18a68,89fe2f86ee3f4fbaa7fb2bf9bd56d088,75f99e6b97d14b14a4e74762ad77391f,89fe2f86ee3f4fbaa7fb2bf9bd56d088'
```

License
-------

[GPLv3](https://www.gnu.org/licenses/gpl-3.0) or later, see
[LICENSE](LICENSE) for more details.

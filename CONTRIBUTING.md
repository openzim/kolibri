# kolibri2zim devel

## contributions

* Open issues, bug reports and send PRs [on github](https://github.com/openzim/kolibri2zim).
* Make sure it's `py3.6+` compatible.
* Use [black](https://github.com/psf/black) code formatting.

## notes

We use `ogv.js`, to play webm videos on browsers that don't support it. Using `video.js`, we default to native playback if supported.

`ogv.js` is an emscripten-based JS decoder for webm and thus dynamically loads differents parts at run-time on platforms that needs them. It has two consequences:


## i18n (to come)

`kolibri2zim` has very minimal non-content text but still uses gettext through [babel](http://babel.pocoo.org/en/latest/index.html) to internationalize.

To add a new locale (`fr` in this example, use only ISO-639-1):

1. init for your locale: `pybabel init -d locale -l fr`
2. make sure the POT is up to date `pybabel extract -o kolibri2zim/locale/messages.pot kolibri2zim`
3. update your locale's catalog `pybabel update -d kolibri2zim/locale/ -l fr -i kolibri2zim/locale/messages.pot`
3. translate the PO file ([poedit](https://poedit.net/) is your friend)
4. compile updated translation `pybabel compile -d kolibri2zim/locale -l fr`

## releasing

* Update your dependencies: `pip install -U setuptools wheel twine`
* Make sure CHANGELOG is up-to-date
* Bump version on `kolibri2zim/VERSION`
* Build packages `python ./setup.py sdist bdist_wheel`
* Upload to PyPI `python -m twine upload dist/kolibri2zim-1.0.0*`.
* Commit your CHANGELOG + version bump changes
* Tag version on git `git tag -a v1.0.0`

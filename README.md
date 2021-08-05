[![Pull Requests Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat)](http://makeapullrequest.com)
[![build status](https://github.com/pelican-plugins/image-preview-thumbnailer/workflows/build/badge.svg)](https://github.com/pelican-plugins/image-preview-thumbnailer/actions?query=workflow%3Abuild)
[![Pypi latest version](https://img.shields.io/pypi/v/pelican-plugin-image-preview-thumbnailer.svg)](https://pypi.python.org/pypi/pelican-plugin-image-preview-thumbnailer)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

[Pelican](https://getpelican.com) plugin TODO


## Installation / setup instructions
To enable this plugin:
1. Install the package from Pypi: `pip install pelican-plugin-image-preview-thumbnailer`
2. Add the plugin to your `pelicanconf.py`:
```python
PLUGINS = [..., 'image_preview_thumbnailer']
```

### Configuration
Available options:

- `IMAGE_PREVIEW_THUMBNAILER_DIR` (optional, default: `thumbnails`) :
  directory where thumbnail images are stored
- `IMAGE_PREVIEW_THUMBNAILER_ENCODING` (optional, default: `utf-8`) :
  encoding to use to parse HTML files
- `IMAGE_PREVIEW_THUMBNAILER_HTML_PARSER` (optional, default: `html.parser`) :
  parse that BEautifulSoup will use to parse HTML files
- `IMAGE_PREVIEW_THUMBNAILER_CERT_VERIFY` (optional, default: `False`) :
  enforce HTTPS certificates verification when sending linkbacks
- `IMAGE_PREVIEW_THUMBNAILER_REQUEST_TIMEOUT` (optional, in seconds, default: `3`) :
  time in seconds allowed for each HTTP linkback request before abandon
- `IMAGE_PREVIEW_THUMBNAILER_USERAGENT` (optional, default: `pelican-plugin-image-preview-thumbnailer`) :
  the `User-Agent` HTTP header to use while sending notifications.


## Contributing

Contributions are welcome and much appreciated. Every little bit helps. You can contribute by improving the documentation,
adding missing features, and fixing bugs. You can also help out by reviewing and commenting on [existing issues](https://github.com/pelican-plugins/image-preview-thumbnailer/issues).

To start contributing to this plugin, review the [Contributing to Pelican](https://docs.getpelican.com/en/latest/contribute.html) documentation,
beginning with the **Contributing Code** section.


### Releasing a new version
With a valid `~/.pypirc`:

1. update `CHANGELOG.md`
2. bump version in `pyproject.toml`
3. `poetry build && poetry publish`
4. perform a release on GitGub, including the description added to `CHANGELOG.md`


## Linter & tests
To execute them:

    pylint *.py
    pytest

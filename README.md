[![Pull Requests Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat)](http://makeapullrequest.com)
[![build status](https://github.com/pelican-plugins/image-preview-thumbnailer/workflows/build/badge.svg)](https://github.com/pelican-plugins/image-preview-thumbnailer/actions?query=workflow%3Abuild)
[![Pypi latest version](https://img.shields.io/pypi/v/pelican-plugin-image-preview-thumbnailer.svg)](https://pypi.python.org/pypi/pelican-plugin-image-preview-thumbnailer)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

[Pelican](https://getpelican.com) plugin that insert thumbnails along image links.

> [!WARNING]
> Since DeviantArt started using CloudFront in 2024, this plugin is not able to produce thumbnails for DeviantArt images.

> However a tested workaround is to use TOR to bypass CloudFront and run the plugin manually on HTML files:
> `torify path/to/image_preview_thumbnailer.py path/to/page.html`

## Demo page
<https://chezsoi.org/lucas/blog/pages/images-libres-de-droits.html>

Source Markdown: [pages/images-libres-de-droits.md](https://github.com/Lucas-C/ludochaordic/blob/master/content/pages/images-libres-de-droits.md)

## Usage instructions
To enable this plugin:
1. Install the package from Pypi: `pip install pelican-plugin-image-preview-thumbnailer`
2. Add the plugin to your `pelicanconf.py`:
```python
PLUGINS = [..., 'image_preview_thumbnailer']
```
3. Enable it on the article / pages you wish by inserting this piece of metadata:
```yaml
Image-preview-thumbnailer: $selector
```

`$selector` is a CSS selector to target HTML elements this plugin will parse and look for `<a>` hyperlinks.
It can be for example `article` if your Pelican template place your pages content in `<article>` tags,
or just `body` to select the whole page.
Several comma-separated values can be provided as CSS selectors to `Image-preview-thumbnailer`.

### Supported link formats
Currently this plugin support preview of the following links:
* "raw" links to GIF/JPEG/PNG images
* links to **Wikipedia/Wikimedia** images
* links to [ArtStation](https://www.artstation.com) artwork pages
* links to [Behance](https://www.behance.net) artwork pages
* links to [Dafont](https://www.dafont.com) font pages
* links to [FreeSVG.org](https://freesvg.org) vector images
* links to [Pixabay](https://pixabay.com) images
* links to pages with a `<meta property="og:image">` or `<meta property="twitter:image">` properties,
  like [DeviantArt](https://www.deviantart.com) artworks, [Flickr](https://www.flickr.com) photos, [https://itch.io](itch.io) pages,
  [OpenGameArt](https://opengameart.org) assets or [WikiArt](https://www.wikiart.org) pages

Feel free to submit PRs to add support for more image hosting websites.

### Only displaying thumbnails on hover
The initial idea for this plugin was to just add `🖼️` icons after links to images,
and then only display thumbnails when hovering on those icons.

To configure this plugin to behave like this, defines the following in your `pelicanconf.py`:
```python
IMAGE_PREVIEW_THUMBNAILER_INSERTED_HTML = '<span class="previewable"> 🖼️</span><img src="{thumb}" class="preview-thumbnail">'
```

And insert those CSS rules:
```css
                     .preview-thumbnail { display: none; }
.previewable:hover + .preview-thumbnail { display: block; }
```

### Usage with images lazyloading
There are various Javascript libraries that can provide images lazyloading.
If your Pelican template make use of one, you can customize `IMAGE_PREVIEW_THUMBNAILER_INSERTED_HTML` in order to benefit from it.

For example, to do so using [lazysizes](https://github.com/aFarkas/lazysizes), defines the following in your `pelicanconf.py`:
```python
IMAGE_PREVIEW_THUMBNAILER_INSERTED_HTML = '''<a href="{link}" target="_blank">
    <div class="lazyload" data-noscript=""><noscript><img src="{thumb}" alt=""></noscript></div>
</a>'''
```

### Configuration
Available `pelicanconf.py` options:

- `IMAGE_PREVIEW_THUMBNAILER_INSERTED_HTML` (optional, default: `<a href="{link}" target="_blank" class="preview-thumbnail"><img src="{thumb}" class="preview-thumbnail"></a>`) :
  the HTML code to be inserted after every link (`<a>`) to an image, in order to preview it
- `IMAGE_PREVIEW_THUMBNAILER_IGNORE_404` (optional, default: `False`) :
  avoid raising exceptions that abort Pelican when links are found, pointing to images, but they end up in HTTP 404 errors
- `SILENT_HTTP_ERRORS` (optional, default: `True`) :
  avoid raising exceptions that abort Pelican when links are found, pointing to images, but they end up with an HTTP error, of any kind. An error log message is still produced.
- `IMAGE_PREVIEW_THUMBNAILER_DIR` (optional, default: `thumbnails`) :
  directory where thumbnail images are stored
- `IMAGE_PREVIEW_THUMBNAILER_EXCEPT_URLS` (optional) :
  comma-separated list of regex patterns of URLs to ignore
- `IMAGE_PREVIEW_THUMBNAILER_THUMB_SIZE` (optional, default: `300`) :
  size in pixel of the generated thumbnails.
- `IMAGE_PREVIEW_THUMBNAILER_ENCODING` (optional, default: `utf-8`) :
  encoding to use to parse HTML files
- `IMAGE_PREVIEW_THUMBNAILER_HTML_PARSER` (optional, default: `html.parser`) :
  parse that BEautifulSoup will use to parse HTML files
- `IMAGE_PREVIEW_THUMBNAILER_CERT_VERIFY` (optional, default: `False`) :
  enforce HTTPS certificates verification when sending linkbacks
- `IMAGE_PREVIEW_THUMBNAILER_REQUEST_TIMEOUT` (optional, in seconds, default: `3`) :
  time in seconds allowed for each HTTP linkback request before abandon
- `IMAGE_PREVIEW_THUMBNAILER_SELECTOR` (optional, default: `body`) :
  CSS selector to target HTML elements this plugin will parse and look for `<a>` hyperlinks.
- `IMAGE_PREVIEW_THUMBNAILER_USERAGENT` (optional, default: `pelican-plugin-image-preview-thumbnailer`) :
  the `User-Agent` HTTP header to use while sending notifications.
- `IMAGE_PREVIEW_THUMBNAILER` (optional, default: `False`) :
  enable the plugin on all your pages

Available metadata entries:
```yaml
image-preview-thumbnailer: $selector or just true
image-preview-thumbnailer-except-urls: same as IMAGE_PREVIEW_THUMBNAILER_EXCEPT_URLS
image-preview-thumbnailer-ignore-404: same as IMAGE_PREVIEW_THUMBNAILER_IGNORE_404
image-preview-thumbnailer-inserted-html: same as IMAGE_PREVIEW_THUMBNAILER_INSERTED_HTML
image-preview-thumbnailer-thumb-size: same as IMAGE_PREVIEW_THUMBNAILER_THUMB_SIZE
```

You will also have to define a `$PIXABAY_API_KEY` environment variable
to download images from [Pixabay](https://pixabay.com).


### Release notes
_cf._ [CHANGELOG.md](CHANGELOG.md)

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

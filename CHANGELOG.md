# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.0.8] - 2022-03-20
### Added
* Adding support for relative image URL in `<meta>` section
* `SILENT_HTTP_ERRORS` configuration entry, set to `True` by default
### Changed
* now URL-decoding thumbnail filenames

## [1.0.7] - 2021-10-14
### Added
* support for links to [Pixabay](https://pixabay.com) images

## [1.0.6] - 2021-09-20
### Added
* support for links to [FreeSVG.org](https://freesvg.org) vector images

## [1.0.4] - 2021-08-18
### Fixed
* `ImportError` with Python 3.6 due to `contextlib.nullcontext` not existing yet

## [1.0.3] - 2021-08-18
### Changed
* several comma-separated values can now be provided as CSS selectors to `Image-preview-thumbnailer`
### Added
* support for pages with a `<meta property="og:image">` or `<meta property="twitter:image">` properties,
  like [DeviantArt](https://www.deviantart.com) artworks, [Flickr](https://www.flickr.com) photos, [https://itch.io](itch.io) pages,
  [OpenGameArt](https://opengameart.org) assets or [WikiArt](https://www.wikiart.org) pages
* support for GIF & SVG images, "bare" or hosted on Wikimedia
* new global `pelicanconf.py` configuration entries:
    + `IMAGE_PREVIEW_THUMBNAILER`
    + `IMAGE_PREVIEW_THUMBNAILER_EXCEPT_URLS`
    + `IMAGE_PREVIEW_THUMBNAILER_IGNORE_404`
    + `IMAGE_PREVIEW_THUMBNAILER_SELECTOR`
* some configuration entries can bow be overriden per article/page:
```yaml
image-preview-thumbnailer-except-urls: ...
image-preview-thumbnailer-ignore-404: ...
image-preview-thumbnailer-inserted-html: ...
image-preview-thumbnailer-thumb-size: ...
```

## [1.0.2] - 2021-08-17
### Added
* support for [Behance](https://www.behance.net), [Dafont](https://www.dafont.com), [Flickr](https://www.flickr.com) & [WikiArt](https://www.wikiart.org) pages

## [1.0.1] - 2021-08-17
### Changed
* `IMAGE_PREVIEW_THUMBNAILER_INSERTED_HTML` now includes a clickable link to the image

## [1.0.0] - 2021-08-16
Initial version released

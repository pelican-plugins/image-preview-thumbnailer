import logging, os, shutil

import pytest
from requests.exceptions import HTTPError

from image_preview_thumbnailer import process_all_links_in_html, PluginConfig, LOGGER


CUR_DIR = os.path.dirname(__file__)
TEST_CONTENT_DIR = os.path.join(CUR_DIR, 'test_content')
BLOG_PAGE_TEMPLATE = """<html lang="en-US">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width">
  <title>Dummy test page</title>
</head>
<body>
  <a href="{illustration_url}">Some link to an illustration</a>
</body>
</html>"""


def setup():
    logging.root.setLevel(logging.DEBUG)
    LOGGER.disable_filter()  # disabling LimitFilter log deduping from pelican.log.FatalLogger
    thumbs_dir = PluginConfig().fs_thumbs_dir()
    shutil.rmtree(thumbs_dir, ignore_errors=True)
    os.makedirs(thumbs_dir)

@pytest.mark.integration
def test_artstation():
    url = 'https://www.artstation.com/artwork/OvE8y'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/OvE8y.jpg") > 0
    assert 'src="thumbnails/OvE8y.jpg"' in out_html

@pytest.mark.integration
def test_behance():
    url = 'https://www.behance.net/gallery/58149803/Character-design-vol-8'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/Character-design-vol-8.jpg") > 0
    assert 'src="thumbnails/Character-design-vol-8.jpg"' in out_html

@pytest.mark.integration
def test_dafont():
    url = 'https://www.dafont.com/mirage-gothic.font?l[]=10&l[]=1'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/mirage-gothic.font.png") > 0
    assert 'src="thumbnails/mirage-gothic.font.png"' in out_html

@pytest.mark.integration
def test_deviantart():
    url = 'https://www.deviantart.com/deevad/art/Krita-texture-speedpainting-test-350472256'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/Krita-texture-speedpainting-test-350472256.jpg") > 0
    assert 'src="thumbnails/Krita-texture-speedpainting-test-350472256.jpg"' in out_html

@pytest.mark.integration
def test_deviantart_mature_content():
    url = 'https://www.deviantart.com/eggboy122/art/Angel-maybe-697980132'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/Angel-maybe-697980132.none") == 0
    assert '<img' not in out_html

@pytest.mark.integration
def test_flickr():
    url = 'https://www.flickr.com/photos/tofuverde/30859168220/'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/30859168220.jpg") > 0
    assert 'src="thumbnails/30859168220.jpg"' in out_html

@pytest.mark.integration
def test_flickr_photostream():
    url = 'https://www.flickr.com/photos/84568447@N00/4860797836/in/photostream/'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/4860797836.jpg") > 0
    assert 'src="thumbnails/4860797836.jpg"' in out_html

@pytest.mark.integration
def test_itchio():
    url = 'https://lucas-c.itch.io/undying-dusk'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/undying-dusk.png") > 0
    assert 'src="thumbnails/undying-dusk.png"' in out_html

@pytest.mark.integration
def test_opengameart():
    url = 'https://opengameart.org/content/kujasa-the-beginning'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/kujasa-the-beginning.jpg") > 0
    assert 'src="thumbnails/kujasa-the-beginning.jpg"' in out_html

@pytest.mark.integration
def test_wikiart():
    url = 'https://www.wikiart.org/en/john-bauer/d-och-d-tog-tomten-tag-i-tyglarna'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/d-och-d-tog-tomten-tag-i-tyglarna.jpg") > 0
    assert 'src="thumbnails/d-och-d-tog-tomten-tag-i-tyglarna.jpg"' in out_html

@pytest.mark.integration
def test_wikimedia():
    url = 'https://commons.wikimedia.org/wiki/File:DnD_Unicorn.png'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/File:DnD_Unicorn.png") > 0
    assert 'src="thumbnails/File:DnD_Unicorn.png"' in out_html

@pytest.mark.integration
def test_bare_jpg():
    url = 'https://durian.blender.org/wp-content/uploads/2009/11/shaman-previz.jpg'
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/shaman-previz.jpg") > 0
    assert 'src="thumbnails/shaman-previz.jpg"' in out_html

@pytest.mark.integration
def test_404():
    url = 'https://example.com/404.jpg'
    with pytest.raises(HTTPError) as exc_info:
        process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert exc_info.value.response.status_code == 404

    config = PluginConfig({'ignore_404': True})
    process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url), config)

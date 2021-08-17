import logging, os, shutil

import httpretty
import pytest

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

def _setup_http_mocks(page_url, html_filepath, img_url):
    with open(os.path.join(TEST_CONTENT_DIR, html_filepath)) as html_file:
        httpretty.register_uri(httpretty.GET, page_url, body=html_file.read(),
                               adding_headers ={'Content-Type': 'text/html'})
    img_filename = img_url.rsplit('/', 1)[1]
    img_ext = os.path.splitext(img_filename)[1]
    content_type = {
        '.gif': 'image/gif',
        '.jpg': 'image/jpeg',
        '.png': 'image/png',
    }[img_ext]
    with open(os.path.join(TEST_CONTENT_DIR, img_filename), 'rb') as img_file:
        httpretty.register_uri(httpretty.GET, img_url, body=img_file.read(),
                               adding_headers ={'Content-Type': content_type})

@httpretty.activate
def test_deviantart_mocked():
    url = 'https://www.deviantart.com/deevad/art/Krita-texture-speedpainting-test-350472256'
    _setup_http_mocks(url, "deviantart.html", "https://images-wixmp-abcdef.wixmp.com/f/LadyofHats_DnD_Unicorn.jpg")
    out_html = process_all_links_in_html(BLOG_PAGE_TEMPLATE.format(illustration_url=url))
    assert os.path.getsize("thumbnails/Krita-texture-speedpainting-test-350472256.jpg") > 0
    assert 'src="thumbnails/Krita-texture-speedpainting-test-350472256.jpg"' in out_html

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

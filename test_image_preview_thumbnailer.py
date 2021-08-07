import logging, os, shutil

import httpretty

from image_preview_thumbnailer import process_all_links_in_html, PluginConfig, LOGGER


CUR_DIR = os.path.dirname(__file__)
TEST_CONTENT_DIR = os.path.join(CUR_DIR, 'test_content')


def setup():
    logging.root.setLevel(logging.DEBUG)
    LOGGER.disable_filter()  # disabling LimitFilter log deduping from pelican.log.FatalLogger
    thumbs_dir = PluginConfig().fs_thumbs_dir()
    shutil.rmtree(thumbs_dir, ignore_errors=True)
    os.makedirs(thumbs_dir)

@httpretty.activate
def test_process_all_links_in_html_deviantart():
    page_url = 'https://www.deviantart.com/deevad/art/Krita-texture-speedpainting-test-350472256'
    _setup_http_mocks(page_url, "deviantart.html", "https://images-wixmp-abcdef.wixmp.com/f/LadyofHats_DnD_Unicorn.jpg")
    config = PluginConfig(selector='body')
    out_html = process_all_links_in_html(f"""
    <html lang="en-US">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width">
      <title>Dummy test page</title>
    </head>
    <body>
      <a href="{page_url}">Some link to a DeviantArt illustration</a>
    </body>""", config)
    assert '<img src="thumbnails/Krita-texture-speedpainting-test-350472256.jpg"/>' in out_html

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

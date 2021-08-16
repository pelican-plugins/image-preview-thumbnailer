import logging, os, re, warnings
from glob import glob
from contextlib import nullcontext
from tempfile import mkstemp

from bs4 import BeautifulSoup
from pelican import signals
from PIL import Image
import requests
from urllib3.exceptions import InsecureRequestWarning


DEFAULT_CERT_VERIFY = True
DEFAULT_ENCODING = 'utf-8'
DEFAULT_HTML_PARSER = 'html.parser'  # Alt: 'html5lib', 'lxml', 'lxml-xml'
DEFAULT_INSERTED_HTML = '<img src="{thumb}">'
DEFAULT_THUMBS_DIR = 'thumbnails'
DEFAULT_THUMB_SIZE = 300
DEFAULT_TIMEOUT = 3
DEFAULT_USER_AGENT = 'pelican-plugin-image-preview-thumbnailer'

LOGGER = logging.getLogger(__name__)


def process_all_links(path, context):
    root_logger_level = logging.root.level
    if root_logger_level > 0:  # inherit root logger level, if defined
        LOGGER.setLevel(root_logger_level)
    content = context.get('article') or context.get('page')
    if not content:
        # This plugin currently does not handle static page, like the index
        # Adding support for them should be trivial though
        return
    selector = content.metadata.get('image-preview-thumbnailer')
    if not selector:
        return
    config = PluginConfig(selector, context)
    if not os.path.exists(config.fs_thumbs_dir()):
        os.makedirs(config.fs_thumbs_dir(), exist_ok=True)
    with nullcontext() if config.cert_verify else warnings.catch_warnings():
        if not config.cert_verify:
            warnings.simplefilter('ignore', InsecureRequestWarning)
        with open(path, "r+", encoding=config.encoding) as html_file:
            edited_html = process_all_links_in_html(html_file, config)
            html_file.seek(0)
            html_file.truncate()
            html_file.write(edited_html)

class PluginConfig:
    def __init__(self, selector='article', settings=None):
        self.selector = selector
        if settings is None:
            settings = {}
        self.output_path = settings.get('OUTPUT_PATH', '')
        self.cert_verify = settings.get('IMAGE_PREVIEW_THUMBNAILER_CERT_VERIFY', DEFAULT_CERT_VERIFY)
        self.encoding = settings.get('IMAGE_PREVIEW_THUMBNAILER_ENCODING', DEFAULT_ENCODING)
        self.html_parser = settings.get('IMAGE_PREVIEW_THUMBNAILER_HTML_PARSER', DEFAULT_HTML_PARSER)
        self.inserted_html = settings.get('IMAGE_PREVIEW_THUMBNAILER_INSERTED_HTML', DEFAULT_INSERTED_HTML)
        self.rel_thumbs_dir = settings.get('IMAGE_PREVIEW_THUMBNAILER_DIR', DEFAULT_THUMBS_DIR)
        self.thumb_size = settings.get('IMAGE_PREVIEW_THUMBNAILER_THUMB_SIZE', DEFAULT_THUMB_SIZE)
        self.timeout = settings.get('IMAGE_PREVIEW_THUMBNAILER_REQUEST_TIMEOUT', DEFAULT_TIMEOUT)
        self.user_agent = settings.get('IMAGE_PREVIEW_THUMBNAILER_USERAGENT', DEFAULT_USER_AGENT)
    def fs_thumbs_dir(self, path=''):
        fs_dir = os.path.join(self.output_path, self.rel_thumbs_dir)
        if path:
            fs_dir = os.path.join(fs_dir, path)
        return fs_dir

def process_all_links_in_html(html_file, config=PluginConfig()):
    soup = BeautifulSoup(html_file, config.html_parser)
    for content in soup.select(config.selector):
        for anchor_tag in content.find_all("a"):
            for url_regex, img_downloader in DOWNLOADERS_PER_URL_REGEX.items():
                match = url_regex.match(anchor_tag['href'])
                if match:
                    process_link(img_downloader, anchor_tag, match, config)
                    break
    return str(soup)

def process_link(img_downloader, anchor_tag, match, config=PluginConfig()):
    thumb_filename = anchor_tag['href'].rsplit('/', 1)[1]
    matching_filepaths = glob(config.fs_thumbs_dir(thumb_filename + '.*'))
    if matching_filepaths:
        fs_thumb_filepath = matching_filepaths[0]
    else:
        LOGGER.info("Thumbnail does not exist => downloading image from %s", anchor_tag['href'])
        tmp_thumb_filepath = img_downloader(match, config)
        if not tmp_thumb_filepath:
            with open(config.fs_thumbs_dir(thumb_filename + '.none'), 'w'):
                pass
            return
        resize_as_thumbnail(tmp_thumb_filepath, config.thumb_size)
        img_ext = os.path.splitext(tmp_thumb_filepath)[1]
        fs_thumb_filepath = config.fs_thumbs_dir(thumb_filename + img_ext)
        os.rename(tmp_thumb_filepath, fs_thumb_filepath)
    if not os.path.getsize(fs_thumb_filepath):
        return
    rel_thumb_filepath = fs_thumb_filepath.replace(config.output_path + '/', '') if config.output_path else fs_thumb_filepath
    # Editing HTML on-the-fly to insert an <img> after the <a>:
    new_elem = BeautifulSoup(config.inserted_html.format(thumb=rel_thumb_filepath), config.html_parser)
    anchor_tag.insert_after(new_elem)

def resize_as_thumbnail(img_filepath, max_size):
    img = Image.open(img_filepath)
    img.thumbnail((max_size, max_size))
    img.save(img_filepath)

def artstation_download_img(match, config=PluginConfig()):
    artwork_url = 'https://www.artstation.com/projects/{}.json'.format(match.group(1))
    resp = http_get(artwork_url, config)
    img_url = resp.json()['assets'][0]['image_url']
    out_filepath = download_img(img_url, config)
    LOGGER.debug("Image downloaded from: %s", img_url)
    return out_filepath

def deviantart_download_img(match, config=PluginConfig()):
    url = match.string
    resp = http_get(url, config)
    if b'Mature Content' in resp.content:
        LOGGER.warning('Mature Content detected on DeviantArt page %s', url)
        return None
    soup = BeautifulSoup(resp.content, config.html_parser)
    img = soup.select_one('main div div div div div div div img')
    if not img:
        LOGGER.error('DeviantArt tag selector failed to find an <img> on %s', url)
    out_filepath = download_img(img['src'], config)
    LOGGER.debug("Image downloaded from: %s", img['src'])
    return out_filepath

def wikipedia_download_img(match, config=PluginConfig()):
    url = match.string
    soup = BeautifulSoup(http_get(url, config).content, config.html_parser)
    anchor_tag = soup.select_one('a.internal')
    if not anchor_tag:
        LOGGER.error('Wikipedia tag selector failed to find a.internal on %s', url)
    img_url = anchor_tag['href']
    if img_url.startswith('//'):
        img_url = 'https:' + img_url
    out_filepath = download_img(img_url, config)
    LOGGER.debug("Image downloaded from: %s", img_url)
    return out_filepath

def download_img(url, config=PluginConfig()):
    if hasattr(url, 'string'):  # can be either a string or a re.Match object
        url = url.string
    resp = http_get(url, config)
    ext = {
        'image/gif': '.gif',
        'image/jpeg': '.jpg',
        'image/png': '.png',
    }[resp.headers['Content-Type']]
    _, out_filepath = mkstemp(ext)
    with open(out_filepath, 'bw') as out_file:
        out_file.write(resp.content)
    return out_filepath

def http_get(url, config=PluginConfig()):
    with requests.get(url, timeout=config.timeout, verify=config.cert_verify,
                           headers={'User-Agent': config.user_agent}) as response:
        if response.status_code != 200 and b'captcha' in response.content:
            LOGGER.warning('CAPTCHA is likely to be required by page %s', url)
        response.raise_for_status()
        return response

DOWNLOADERS_PER_URL_REGEX = {
    re.compile(r'https://www.artstation.com/artwork/(.+)'): artstation_download_img,
    re.compile(r'https://www.deviantart.com/.+/art/.+'): deviantart_download_img,
    re.compile(r'.+wiki(m|p)edia.org/wiki/.+(jpg|png)'): wikipedia_download_img,
    re.compile(r'.+\.(gif|jpe?g|png)'): download_img,
}

def register():
    signals.content_written.connect(process_all_links)

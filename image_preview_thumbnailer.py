from contextlib import closing, nullcontext
import logging, re, warnings

from bs4 import BeautifulSoup
from pelican import signals
import requests
from urllib3.exceptions import InsecureRequestWarning


DEFAULT_CERT_VERIFY = False
DEFAULT_DIR = 'thumbnails'
DEFAULT_ENCODING = 'utf-8'
DEFAULT_HTML_PARSER = 'html.parser'  # Alt: 'html5lib', 'lxml', 'lxml-xml'
DEFAULT_TIMEOUT = 3
DEFAULT_USER_AGENT = 'pelican-plugin-image-preview-thumbnailer'

LOGGER = logging.getLogger(__name__)


def process_all_images(path, context):
    root_logger_level = logging.root.level
    if root_logger_level > 0:  # inherit root logger level, if defined
        LOGGER.setLevel(root_logger_level)
    config = PluginConfig(context)
    with warnings.catch_warnings() if config.cert_verify else nullcontext():
        if config.cert_verify:
            warnings.simplefilter('ignore', InsecureRequestWarning)
        with open(path, "r+", encoding=config.encoding) as html_file:
            edited_html = process_all_images_in_fragment(html_file, config)
            html_file.seek(0)
            html_file.truncate()
            html_file.write(edited_html)

class PluginConfig:
    def __init__(self, settings=None):
        if settings is None:
            settings = {}
        self.siteurl = settings.get('SITEURL', '')
        self.cert_verify = settings.get('IMAGE_PREVIEW_THUMBNAILER_CERT_VERIFY', DEFAULT_CERT_VERIFY)
        self.encoding = settings.get('IMAGE_PREVIEW_THUMBNAILER_ENCODING', DEFAULT_ENCODING)
        self.dir = settings.get('IMAGE_PREVIEW_THUMBNAILER_DIR', DEFAULT_DIR)
        self.html_parser = settings.get('IMAGE_PREVIEW_THUMBNAILER_HTML_PARSER', DEFAULT_HTML_PARSER)
        self.timeout = settings.get('IMAGE_PREVIEW_THUMBNAILER_REQUEST_TIMEOUT', DEFAULT_TIMEOUT)
        self.user_agent = settings.get('IMAGE_PREVIEW_THUMBNAILER_USERAGENT', DEFAULT_USER_AGENT)

def process_all_images_in_fragment(html_file, config):
    soup = BeautifulSoup(html_file, config.html_parser)
    for anchor_tag in soup.find_all("a"):
        for url_regex, downloader in DOWNLOADERS_PER_URL_REGEX.items():
            if url_regex.match(anchor_tag['href']):
                # 1. Thumbnail already exists?
                # 1a. false => download image & thumbnail it
                downloader.download_image(anchor_tag['href'])
                # 2. Edit HTML on-the-fly
                break
    return str(soup)


class DeviantArtDownloader:
    def download_image(self, url):
        LOGGER.info("Downloading image from %s", url)  # TODO


GET_CHUNK_SIZE = 2**10
MAX_RESPONSE_LENGTH = 2**20
def requests_get_with_max_size(url, config=PluginConfig()):
    '''
    We cap the allowed response size, in order to make things faster and avoid downloading useless huge blobs of data
    cf. https://benbernardblog.com/the-case-of-the-mysterious-python-crash/
    '''
    with closing(requests.get(url, stream=True, timeout=config.timeout, verify=config.cert_verify,
                              headers={'User-Agent': config.user_agent})) as response:
        response.raise_for_status()
        content = ''
        for chunk in response.iter_content(chunk_size=GET_CHUNK_SIZE, decode_unicode=True):
            content += chunk if response.encoding else chunk.decode()
            if len(content) >= MAX_RESPONSE_LENGTH:
                # Even truncated, the output is maybe still parsable as HTML, so we do not abort and still return the content.
                LOGGER.warning("The response for URL %s was too large, and hence was truncated to %s bytes.", url, MAX_RESPONSE_LENGTH)
                break
        return content, response.headers

DOWNLOADERS_PER_URL_REGEX = {
    re.compile('https://www.deviantart.com/.+/art/.+'): DeviantArtDownloader()
}

def register():
    signals.content_written.connect(process_all_images)

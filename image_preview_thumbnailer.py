import logging, os, re, warnings
from glob import glob
from contextlib import nullcontext
from tempfile import mkstemp

from bs4 import BeautifulSoup
from pelican import signals
from PIL import Image
import requests
from requests.exceptions import ConnectTimeout
from urllib3.exceptions import InsecureRequestWarning


DEFAULT_CERT_VERIFY = True
DEFAULT_ENCODING = 'utf-8'
DEFAULT_HTML_PARSER = 'html.parser'  # Alt: 'html5lib', 'lxml', 'lxml-xml'
DEFAULT_IGNORE_404 = False
DEFAULT_INSERTED_HTML = '<a href="{link}" target="_blank" class="preview-thumbnail"><img src="{thumb}" class="preview-thumbnail"></a>'
DEFAULT_SELECTOR = 'body'
DEFAULT_THUMBS_DIR = 'thumbnails'
DEFAULT_THUMB_SIZE = 300
DEFAULT_TIMEOUT = 3
DEFAULT_USER_AGENT = 'pelican-plugin-image-preview-thumbnailer'

EXT_PER_CONTENT_TYPE = {
    'image/gif': '.gif',
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/png': '.png',
    'image/svg+xml': '.svg',
}

LOGGER = logging.getLogger(__name__)


def process_all_links(path, context):
    if logging.root.level > 0:  # inherit root logger level, if defined
        LOGGER.setLevel(logging.root.level)
    content = context.get('article') or context.get('page')
    if not content:
        # This plugin currently does not handle static page, like the index
        # Adding support for them should be trivial though
        return
    config = PluginConfig.from_metadata(content.metadata, context)
    if not config:  # => this plugin has not been enabled on this page
        return
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

class PluginConfig(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    def __init__(self, odict=None):
        super().__init__(odict or {})
        self.setdefault('output_path', '')
        self.setdefault('cert_verify', DEFAULT_CERT_VERIFY)
        self.setdefault('encoding', DEFAULT_ENCODING)
        self.setdefault('except_urls', '')
        self.setdefault('html_parser', DEFAULT_HTML_PARSER)
        self.setdefault('ignore_404', DEFAULT_IGNORE_404)
        self.setdefault('inserted_html', DEFAULT_INSERTED_HTML)
        self.setdefault('rel_thumbs_dir', DEFAULT_THUMBS_DIR)
        self.setdefault('selector', DEFAULT_SELECTOR)
        self.setdefault('thumb_size', DEFAULT_THUMB_SIZE)
        self.setdefault('timeout', DEFAULT_TIMEOUT)
        self.setdefault('user_agent', DEFAULT_USER_AGENT)
        # pylint: disable=access-member-before-definition
        if self.except_urls and isinstance(self.except_urls, str):
            self.except_urls = [re.compile(regex) for regex in self.except_urls.split(',')]
        if isinstance(self.selector, str):
            self.selector = self.selector.split(',')
    @classmethod
    def from_metadata(cls, metadata, settings):
        enabled = metadata.get('image-preview-thumbnailer') or settings.get('IMAGE_PREVIEW_THUMBNAILER')
        if not enabled:
            return None
        if settings is None:
            settings = {}
        attrs = {}
        def set_attr(key, value):
            if value is not None:
                attrs[key] = value
        set_attr('output_path', settings.get('OUTPUT_PATH'))
        # Global configuration entries:
        set_attr('cert_verify', settings.get('IMAGE_PREVIEW_THUMBNAILER_CERT_VERIFY'))
        set_attr('encoding', settings.get('IMAGE_PREVIEW_THUMBNAILER_ENCODING'))
        set_attr('html_parser', settings.get('IMAGE_PREVIEW_THUMBNAILER_HTML_PARSER'))
        set_attr('rel_thumbs_dir', settings.get('IMAGE_PREVIEW_THUMBNAILER_DIR'))
        set_attr('timeout', settings.get('IMAGE_PREVIEW_THUMBNAILER_REQUEST_TIMEOUT'))
        set_attr('user_agent', settings.get('IMAGE_PREVIEW_THUMBNAILER_USERAGENT'))
        # Configuration entries that can be configured either globally or per article/page:
        set_attr('selector', (enabled if enabled is not True else None) or settings.get('IMAGE_PREVIEW_THUMBNAILER_SELECTOR'))
        set_attr('except_urls', metadata.get('image-preview-thumbnailer-except-urls') or settings.get('IMAGE_PREVIEW_THUMBNAILER_EXCEPT_URLS'))
        set_attr('ignore_404', metadata.get('image-preview-thumbnailer-ignore-404') or settings.get('IMAGE_PREVIEW_THUMBNAILER_IGNORE_404'))
        set_attr('inserted_html', metadata.get('image-preview-thumbnailer-inserted-html') or settings.get('IMAGE_PREVIEW_THUMBNAILER_INSERTED_HTML'))
        set_attr('thumb_size', metadata.get('image-preview-thumbnailer-thumb-size') or settings.get('IMAGE_PREVIEW_THUMBNAILER_THUMB_SIZE'))
        return cls(attrs)
    def fs_thumbs_dir(self, path=''):
        fs_dir = os.path.join(self.output_path, self.rel_thumbs_dir)
        if path:
            fs_dir = os.path.join(fs_dir, path)
        return fs_dir

def process_all_links_in_html(html_file, config=PluginConfig()):
    soup = BeautifulSoup(html_file, config.html_parser)
    anchor_tags = set()
    for css_selector in config.selector:
        for content in soup.select(css_selector):
            for anchor_tag in content.find_all("a"):
                if not anchor_tag['href'].startswith('http'):
                    continue  # internal links are not supported for now
                if any(regex.search(anchor_tag['href']) for regex in config.except_urls):
                    continue
                anchor_tags.add(anchor_tag)
    for anchor_tag in anchor_tags:
        for url_regex, img_downloader in DOWNLOADERS_PER_URL_REGEX.items():
            url_match = url_regex.match(anchor_tag['href'])
            if url_match:
                process_link(img_downloader, anchor_tag, url_match, config)
                break  # no need to test other image downloaders
        else:
            process_link(meta_img_downloader, anchor_tag, anchor_tag['href'], config)
    return str(soup)

def process_link(img_downloader, anchor_tag, url_match, config=PluginConfig()):
    thumb_filename = extract_thumb_filename(anchor_tag['href'])
    matching_filepaths = glob(config.fs_thumbs_dir(thumb_filename + '.*'))
    if matching_filepaths:  # => a thumbnail has already been generated
        fs_thumb_filepath = matching_filepaths[0]
    else:
        LOGGER.info("Thumbnail does not exist => downloading image from %s", anchor_tag['href'])
        tmp_thumb_filepath = img_downloader(url_match, config)
        if not tmp_thumb_filepath:  # => means the downloader failed to retrieve the image in a "supported" case
            with open(config.fs_thumbs_dir(thumb_filename + '.none'), 'w'):
                pass
            return
        img_ext = os.path.splitext(tmp_thumb_filepath)[1]
        if img_ext != '.svg':  # Pillow cannot read SVG files
            resize_as_thumbnail(tmp_thumb_filepath, config.thumb_size)
        fs_thumb_filepath = config.fs_thumbs_dir(thumb_filename + img_ext)
        os.rename(tmp_thumb_filepath, fs_thumb_filepath)
    if not os.path.getsize(fs_thumb_filepath):  # .none file, meaning no thumbnail could be donwloaded
        return
    rel_thumb_filepath = fs_thumb_filepath.replace(config.output_path + '/', '') if config.output_path else fs_thumb_filepath
    # Editing HTML on-the-fly to insert an <img> after the <a>:
    new_elem_html = config.inserted_html.format(thumb=rel_thumb_filepath, link=anchor_tag['href'])
    anchor_tag.insert_after(BeautifulSoup(new_elem_html, config.html_parser))

def extract_thumb_filename(page_url):
    url_frags = page_url.split('/')
    thumb_filename = url_frags.pop()
    # Workarounds for DeviantArt & Flickr URL naming scheme:
    while thumb_filename in ('', 'gallery', 'in', 'photostream'):
        thumb_filename = url_frags.pop()
        if thumb_filename.startswith('album-'):  # Workaround for Flickr photostream URLs
            thumb_filename = url_frags.pop()
    thumb_filename = thumb_filename.split('#', 1)[0].split('?', 1)[0]
    if any(thumb_filename.endswith(ext) for ext in EXT_PER_CONTENT_TYPE.values()):
        thumb_filename = os.path.splitext(thumb_filename)[0]
    return thumb_filename

def resize_as_thumbnail(img_filepath, max_size):
    img = Image.open(img_filepath)
    img.thumbnail((max_size, max_size))
    img.save(img_filepath)

def artstation_download_img(url_match, config=PluginConfig()):
    artwork_url = 'https://www.artstation.com/projects/{}.json'.format(url_match.group(1))
    resp = http_get(artwork_url, config)
    if not resp:
        return None
    img_url = resp.json()['assets'][0]['image_url']
    out_filepath = download_img(img_url, config)
    LOGGER.debug("Image downloaded from: %s", img_url)
    return out_filepath

def behance_download_img(url_match, config=PluginConfig()):
    # API key from https://github.com/djheru/js-behance-api
    artwork_url = 'https://www.behance.net/v2/projects/{}?api_key=NdTKNWys9AdBhxMhXnKuxgfzmqvwkg55'.format(url_match.group(1))
    resp = http_get(artwork_url, config)
    if not resp:
        return None
    img_url = resp.json()['project']['covers']['404']
    out_filepath = download_img(img_url, config)
    LOGGER.debug("Image downloaded from: %s", img_url)
    return out_filepath

def dafont_download_img(url_match, config=PluginConfig()):
    url = url_match.string
    resp = http_get(url, config)
    if not resp:
        return None
    soup = BeautifulSoup(resp.content, config.html_parser)
    preview_div = soup.select_one('.preview') or soup.select_one('.preview_l')
    if not preview_div:
        raise RuntimeError('Dafont tag selector failed to find a .preview or .preview_l <div> on ' + url)
    img_url = preview_div['style'].replace('background-image:url(', '').replace(')', '')
    if img_url.startswith('//'):
        img_url = 'https:' + img_url
    elif not img_url.startswith('http'):
        img_url = 'https://www.dafont.com' + img_url
    out_filepath = download_img(img_url, config)
    LOGGER.debug("Image downloaded from: %s", img_url)
    return out_filepath

def deviantart_download_img(url_match, config=PluginConfig()):
    img_url = _meta_img_url(url_match.string, config)
    if not img_url or img_url.endswith('noentrythumb-200.png'):  # displayed e.g. for mature content
        return None
    out_filepath = download_img(img_url, config)
    LOGGER.debug("Image downloaded from: %s", img_url)
    return out_filepath

def wikipedia_download_img(url_match, config=PluginConfig()):
    url = url_match.string
    resp = http_get(url, config)
    if not resp:
        return None
    soup = BeautifulSoup(resp.content, config.html_parser)
    anchor_tag = soup.select_one('a.internal')
    if not anchor_tag:
        raise RuntimeError('Wikipedia tag selector failed to find an .internal <a> on ' + url)
    img_url = anchor_tag['href']
    if img_url.startswith('//'):
        img_url = 'https:' + img_url
    out_filepath = download_img(img_url, config)
    LOGGER.debug("Image downloaded from: %s", img_url)
    return out_filepath

def meta_img_downloader(url, config=PluginConfig()):
    img_url = _meta_img_url(url, config)
    if not img_url:
        return None
    safe_config = PluginConfig(config)  # copy
    # pylint: disable=attribute-defined-outside-init
    safe_config.ignore_404 = True
    try:
        out_filepath = download_img(img_url, safe_config)
        LOGGER.debug("Image downloaded from: %s", img_url)
        return out_filepath
    except ConnectTimeout:
        return None

def _meta_img_url(url, config):
    resp = http_get(url, config)
    if not resp:
        return None
    soup = BeautifulSoup(resp.content, config.html_parser)
    meta = soup.select_one('meta[property="og:image"]') or soup.select_one('meta[property="twitter:image"]')
    return meta and meta['content']

def download_img(url, config=PluginConfig()):
    if hasattr(url, 'string'):  # can initialy be either a string or a re.Match object
        url = url.string
    resp = http_get(url, config)
    if not resp:
        return None
    ext = EXT_PER_CONTENT_TYPE[resp.headers['Content-Type']]
    _, out_filepath = mkstemp(ext)
    with open(out_filepath, 'bw') as out_file:
        out_file.write(resp.content)
    return out_filepath

def http_get(url, config=PluginConfig()):
    with requests.get(url, timeout=config.timeout, verify=config.cert_verify,
                           headers={'User-Agent': config.user_agent}) as response:
        if response.status_code == 404 and config.ignore_404:
            return None
        if response.status_code != 200 and b'captcha' in response.content:
            LOGGER.warning('CAPTCHA is likely to be required by page %s', url)
        response.raise_for_status()
        return response

DOWNLOADERS_PER_URL_REGEX = {
    re.compile(r'https://www\.artstation\.com/artwork/(.+)'): artstation_download_img,
    re.compile(r'https://www\.behance\.net/gallery/(.+)/.+'): behance_download_img,
    re.compile(r'https://www\.dafont\.com/.+\.font.*'): dafont_download_img,
    re.compile(r'https://www\.deviantart\.com/.+/art/.+'): deviantart_download_img,
    re.compile(r'.+wiki(m|p)edia\.org/wiki/.+(gif|jpg|png|svg)$'): wikipedia_download_img,
    re.compile(r'.+\.(gif|jpe?g|png|svg)$'): download_img,
}

def register():
    signals.content_written.connect(process_all_links)

import os, shutil
import logging
import time

import imgkit
from PIL import Image, ImageOps
import image_slicer
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from splinter import Browser
import config
from utils import utils

webdriver_options = Options()
webdriver_options.headless = True
webdriver_options.add_argument('enable-automation')
webdriver_options.add_argument('--no-sandbox')
webdriver_options.add_argument('--window-size=1920,1080')
webdriver_options.add_argument('--headless')
webdriver_options.add_argument('--disable-gpu')
webdriver_options.add_argument('--disable-dev-shm-usage')
webdriver_options.add_argument('--hide-scrollbars')
webdriver_options.add_argument('--disable-extensions')
webdriver_options.add_argument('--dns-prefetch-disable')
webdriver_options.add_argument('--force-device-scale-factor=1')
webdriver_options.add_argument('--disable-setuid-sandbox')
webdriver_options.add_argument('--disable-browser-side-navigation')
webdriver_options.add_argument('enable-features=NetworkService')

firefox_options = FirefoxOptions()
firefox_options.headless = True
firefox_options.log.level = "trace"  # Debug
firefox_options.add_argument('enable-automation')
firefox_options.add_argument('--no-sandbox')
firefox_options.add_argument('--window-size=1920,1080')
firefox_options.add_argument('--headless')
firefox_options.add_argument('--disable-gpu')
firefox_options.add_argument('--disable-dev-shm-usage')
firefox_options.add_argument('--hide-scrollbars')
firefox_options.add_argument('--disable-extensions')
firefox_options.add_argument('--dns-prefetch-disable')

FIREFOX_BINARY = FirefoxBinary('/opt/firefox/firefox')
# FireFox PROFILE
PROFILE = webdriver.FirefoxProfile()
PROFILE.set_preference("browser.cache.disk.enable", False)
PROFILE.set_preference("browser.cache.memory.enable", False)
PROFILE.set_preference("browser.cache.offline.enable", False)
PROFILE.set_preference("network.http.use-cache", False)
PROFILE.set_preference("general.useragent.override",
                       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) Gecko/20100101 Firefox/72.0")


GECKODRIVER_LOG = '/tmp/geckodriver.log'
CHROMEDRIVER_LOG = '/tmp/chromedriver.log'

render_url = 'https://{}/index.php?route=photobook/photobook/renderPage&uid={}&page={}'
default_size = {'width': 2000, 'height': 1000}

logger = logging.getLogger()

domains_dict = utils.load_domains_dict()


def create_destination_file_for_preview(domain, uid, filename=None, include_os_path=True):
    try:
        path = os.path.join(domains_dict.get(domain) if include_os_path is True else domain,
                            'image/photobook/snapshots', uid)
    except KeyError:
        return None

    try:
        if not os.path.exists(path):
            os.makedirs(path)
            os.chmod(path, 0o777)
    except:
        pass
    if filename is None:
        return path
    return os.path.join(path, '{}.jpg'.format(filename))


def create_destination_file_for_render(domain, uid, filename=None, include_os_path=True):
    try:
        path = os.path.join(domains_dict.get(domain) if include_os_path is True else domain, 'image/photobook/renders',
                            uid)
    except KeyError:
        return None

    if not os.path.exists(path):
        os.makedirs(path)
        os.chmod(path, 0o777)
    if filename is None:
        return path
    return os.path.join(path, '{}.png'.format(filename))


def slice(path):
    '''
    divide image into two parts
    :param path: path of image
    :return:
    '''
    img = Image.open(path)
    width, height = img.size
    res = (img.crop((0, 0, width / 2, height)), img.crop((width / 2, 0, width, height)))
    return res


def slice_page(page, pages, domain, uid):
    original = create_destination_file_for_preview(domain, uid, '{}-full'.format(page))
    sliced = image_slicer.slice(original, 2, save=False)

    #slice(original)
    width, height = sliced[0].image.size
    border_size = int(height - height / 1.02040)
    if page == 1:
        sliced[0].image.save(create_destination_file_for_preview(domain, uid, '{}-original'.format(pages * 2)))
        sliced[1].image.crop((0, 0, width - 3, height)) \
            .save(create_destination_file_for_preview(domain, uid, '1-original'))

        # sliced[0].image.crop((10, 10, 500, 500 - 10)).save(create_destination_file_for_preview(domain, uid, pages * 2), quality=100)
        # sliced[1].image.crop((10, 10, 500, 500 - 10)).save(create_destination_file_for_preview(domain, uid, 1), quality=100)
        sliced[0].image.crop((0, 0, width, height - 0)) \
            .save(create_destination_file_for_preview(domain, uid, pages * 2), quality=100)

        sliced[1].image.crop((0, 0, width - 3, height - 0)) \
            .save(create_destination_file_for_preview(domain, uid, 1), quality=100)

    else:
        number = page - 2 + page
        if number != 2:
            sliced[0].image.crop((border_size, border_size, width, height - border_size)).save(
                create_destination_file_for_preview(domain, uid, number), quality=100)
        else:
            sliced[0].image.save(create_destination_file_for_preview(domain, uid, number), quality=100)

        if number + 1 != pages * 2 - 1:
            sliced[1].image.crop((0, border_size, width - border_size, height - border_size)).save(
                create_destination_file_for_preview(domain, uid, number + 1), quality=100)
        else:
            sliced[1].image.save(create_destination_file_for_preview(domain, uid, number + 1), quality=100)

    os.remove(original)
    print('Progress: {}%'.format(int(100 / pages * page)))
    # sys.stdout.write("\033[F")
    # sys.stdout.write("\033[K")


def create_borders(pages, domain, uid):
    # left canvas

    cover_right = Image.open(create_destination_file_for_preview(domain, uid, '{}-original'.format(1)))
    left_image = Image.open(create_destination_file_for_preview(domain, uid, 2))

    border_size = int(cover_right.size[1] - cover_right.size[1] / 1.02040)
    bottom_box = (0, cover_right.size[1] - border_size, cover_right.size[0], cover_right.size[1])
    top_box = (0, 0, cover_right.size[0], border_size)
    left_box = (cover_right.size[0] - border_size - 5, 0, cover_right.size[0], cover_right.size[1])

    bottom_region = ImageOps.flip(ImageOps.mirror(cover_right.crop(bottom_box)))
    top_region = ImageOps.flip(ImageOps.mirror(cover_right.crop(top_box)))
    left_region = cover_right.crop(left_box)

    left_image.paste(bottom_region, (0, left_image.size[1] - border_size))
    left_image.paste(top_region, (0, 0))
    left_image.paste(left_region, (0, 0))

    left_image.save(create_destination_file_for_preview(domain, uid, 2), quality=100)

    # right canvas
    cover_left = Image.open(create_destination_file_for_preview(domain, uid, '{}-original'.format(pages * 2)))
    right_image = Image.open(create_destination_file_for_preview(domain, uid, pages * 2 - 1))

    bottom_box = (0, cover_left.size[1] - border_size, cover_left.size[0], cover_left.size[1])
    top_box = (0, 0, cover_left.size[0], border_size)
    right_box = (0, 0, cover_left.size[0] - border_size - 5, cover_left.size[1])

    bottom_region = ImageOps.flip(ImageOps.mirror(cover_left.crop(bottom_box)))
    top_region = ImageOps.flip(ImageOps.mirror(cover_left.crop(top_box)))
    right_region = cover_left.crop(right_box)

    right_image.paste(bottom_region, (0, right_image.size[1] - border_size))
    right_image.paste(top_region, (0, 0))
    right_image.paste(right_region, (right_image.size[0] - border_size - 5, 0))

    right_image.save(create_destination_file_for_preview(domain, uid, pages * 2 - 1), quality=100)
    os.remove(create_destination_file_for_preview(domain, uid, '{}-original'.format(1)))
    os.remove(create_destination_file_for_preview(domain, uid, '{}-original'.format(pages * 2)))


def create_response(destination, url_path):
    f = []
    for (dirpath, dirnames, filenames) in os.walk(destination):
        [f.extend([os.path.join(url_path, file)]) for file in filenames]
        break
    logger.info(f"Sending http response...")
    return {'data': f, 'code': 200}


def to_bool(value):
    valid = {'true': True, 't': True, '1': True,
             'false': False, 'f': False, '0': False,
             }

    if isinstance(value, bool):
        return value

    lower_value = value.lower()
    if lower_value in valid:
        return valid[lower_value]
    else:
        raise ValueError('invalid literal for boolean: "%s"' % value)


def make_previews(pages=0, uid='', domain='', size=None, is_user_preview=False):
    """
    Generate preview of book
    :param pages: number of pages
    :param uid: uid of book
    :param domain: site url, where book was created
    :param size: size of final image
    :param is_user_preview: indicate if it's user's book
    :return:
    """
    logger.info(f"Creating previews for {domain}, uid: {uid}, pages: {pages}")

    total_start_time = time.time()

    if create_destination_file_for_preview(domain, uid) is None:
        return {'message': "Unregistered domain name received", 'code': 400}

    if size is None:
        size = default_size
    page = 1

    if config.APP_ENV == 'production':
        preview_driver = webdriver.Chrome(options=webdriver_options)
    else:
        preview_driver = webdriver.Chrome(ChromeDriverManager().install(), options=webdriver_options)

    preview_driver.set_window_size(size['width'], size['height'])
    while page <= pages:

        if is_user_preview is False:
            destination = create_destination_file_for_preview(domain, uid, '{}-full'.format(page))
        else:
            destination = create_destination_file_for_preview(domain, '%s/%s' % (uid, 'preview'), page)

        url = render_url.format(domain, uid, page - 1)
        url = url + '&width={}&height={}'.format(size['width'], size['height'])

        start_time = time.time()
        try:
            options = {
                'window-status': 'ready',
                'quiet': '',
                'quality': 100,
                'images': '',
                'zoom': 1,
                'format': 'jpg'
            }
            options.update(size)
            logger.info(f"Generating preview image from page: {url}")
            #imgkit.from_url(url, destination, options=options)
            preview_driver.get(url)
            element = preview_driver.find_element(By.TAG_NAME, 'body')
            element.screenshot(destination)
        except Exception as e:
            logger.error(f"Can't create screenshot for preview, uid: {uid}", e)
            return {'message': "Error occurred while render image with wkhtmltoimage", 'code': 404}


        image = Image.open(destination)
        image.convert("RGB").save(destination, quality=80)
        os.chmod(destination, 0o777)
        # if rendering user's book
        # save it to preview dir without slicing
        if is_user_preview is False:
            slice_page(page, pages, domain, uid)

        page = page + 1

    # driver.quit()
    logger.info(f"Generating preview finished in {time.time() - total_start_time} seconds, uid: {uid}")
    preview_driver.quit()
    # if is user's book render
    # don't create borders
    if is_user_preview is False:
        create_borders(pages, domain, uid)
        return create_response(
            create_destination_file_for_preview(domain, uid),
            create_destination_file_for_preview(domain, uid, None, False)
        )
    else:
        return create_response(
            create_destination_file_for_preview(domain, '%s/%s' % (uid, 'preview')),
            create_destination_file_for_preview(domain, '%s/%s' % (uid, 'preview'), None, False)
        )


def render_book(uid='', domain='', size=None, pages=0, no_border=False):
    logger.info(f"Got request for rendering book with uid: {uid}")
    total_start_time = time.time()
    if create_destination_file_for_preview(domain, uid) is None:
        return {'message': "Unregistered domain name received", 'code': 400}

    try:
        path = os.path.join(domains_dict.get(domain), 'image/photobook/renders', uid)
    except KeyError as e:
        logger.error("Error when creating image path", e)
        return None

    if os.path.exists(path):
        shutil.rmtree(path)

    if size is None:
        size = default_size

    border_offset = 100
    if no_border:
        border_offset = 0
    # add offset for pattern's borders
    size['width'] += border_offset * 2
    size['height'] += border_offset
    page = 0

    cap = DesiredCapabilities().FIREFOX
    cap["marionette"] = False

    logger.info(f"Initializing web driver...")
    # render_driver = webdriver.Firefox(firefox_profile=PROFILE,
    #                                   #executable_path='/usr/bin/geckodriver',
    #                                   capabilities=cap,
    #                                    #service_log_path=GECKODRIVER_LOG,
    #                                    service_args=["--marionette-port", "2828"],
    #                                   options=firefox_options)


    if config.APP_ENV == 'production':
        render_driver = webdriver.Chrome(options=webdriver_options, service_log_path=CHROMEDRIVER_LOG)
    else:
        render_driver = webdriver.Chrome(ChromeDriverManager().install(), options=webdriver_options,
                                         service_log_path=CHROMEDRIVER_LOG)

    render_driver.set_window_size(size['width'], size['height'])
    render_driver.set_page_load_timeout(120)
    render_driver.set_script_timeout(120)
    logger.info(f"Web driver has been initialized")

    options = {
        'window-status': 'ready',
        'quiet': '',
        'quality': 100,
        'images': '',
        'zoom': 1,
        'format': 'jpg'
    }
    options.update(size)

    while page < pages:
        destination_file = create_destination_file_for_render(domain, uid, page)

        url = render_url.format(domain, uid, page)
        url = url + '&isFullRender=true&width={}&height={}'.format(size['width'] - border_offset * 2,
                                                                   size['height'] - border_offset)
        start_time = time.time()
        try:

            logger.info(f"Generating image from page: {url} using imgkit")
            #imgkit.from_url(url, destination_file, options=options)

            render_driver.get(url)
            element = render_driver.find_element(By.TAG_NAME, 'body')
            element.screenshot(destination_file)
            logger.info(f"DEST: {destination_file}")
            #destination_file = element.screenshot(destination_file, full=True)

        except Exception as e:
            logger.error(f"Can't generate screenshot from book page: {url}, took {time.time() - start_time} seconds", e)
            logger.info(f"Error when using chrome driver. Trying to generate image with imgkit")
            imgkit.from_url(url, destination_file, options=options)
            #return {'message': "Error occurred while render image with wkhtmltoimage", 'code': 404}
        logger.info(f"Generating screenshot took: {time.time() - start_time} seconds. Sleep for 3 seconds....")
        time.sleep(3)
        image = Image.open(destination_file)
        os.remove(destination_file)

        destination_file = destination_file.replace('.png', '.jpg')
        logger.info(f"Saving image to: {destination_file}")

        image.convert("RGB").save(destination_file, quality=100, dpi=(600, 600))
        os.chmod(destination_file, 0o777)

        logger.info(f"Image saved to: {destination_file}")
        logger.info(f"Rendering progress: {format(int(100 / pages * page))}%")
        # sys.stdout.write("\033[F")
        # sys.stdout.write("\033[K")
        page = page + 1
        render_driver.refresh()
    render_driver.quit()
    logger.info(f"Rendering progress: 100%, finished in {time.time() - total_start_time} seconds")
    return create_response(
        create_destination_file_for_render(domain, uid),
        create_destination_file_for_render(domain, uid, None, False)
    )

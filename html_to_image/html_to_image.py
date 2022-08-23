import os, shutil
import logging
import time
from PIL import Image, ImageOps
import image_slicer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

import config
from utils import utils

chrome_options = Options()
chrome_options.headless = True
chrome_options.add_argument('enable-automation')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--hide-scrollbars')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--dns-prefetch-disable')

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
    return os.path.join(path, '{}.jpg'.format(filename))


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
        preview_driver = webdriver.Chrome(options=chrome_options)
    else:
        preview_driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

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
            # imgkit.from_url(url, destination, options=options)
            logger.info(f"Generating preview image from page: {url}")
            preview_driver.get(url)
            element = preview_driver.find_element(By.TAG_NAME, 'body')
            element.screenshot(destination)
        except Exception as e:
            logger.error(f"Can't create screenshot for preview, uid: {uid}", e)
            return {'message': "Error occurred while render image with wkhtmltoimage", 'code': 404}

        response_start = preview_driver.execute_script("return window.performance.timing.responseStart")
        dom_complete = preview_driver.execute_script("return window.performance.timing.domComplete")
        loading_time = dom_complete - response_start

        logger.info(f"Generating preview for {uid} took: {time.time() - start_time} seconds. "
                    f"Page loaded  in: {loading_time} seconds")

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

    if config.APP_ENV == 'production':
        render_driver = webdriver.Chrome(options=chrome_options)
    else:
        render_driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    render_driver.set_window_size(size['width'], size['height'])
    render_driver.set_page_load_timeout(30)
    #render_driver.save_screenshot()
    while page < pages:
        destination_file = create_destination_file_for_render(domain, uid, page)

        url = render_url.format(domain, uid, page)
        url = url + '&isFullRender=true&width={}&height={}'.format(size['width'] - border_offset * 2,
                                                                   size['height'] - border_offset)
        start_time = time.time()
        try:
            logger.info(f"Generating image from page: {url}")
            render_driver.get(url)
            #element = render_driver.find_element(By.TAG_NAME, 'body')
            render_driver.save_screenshot(destination_file)
        except Exception as e:
            logger.error(f"Can't generate screenshot from book page: {url}", e)
            return {'message': "Error occurred while render image with wkhtmltoimage", 'code': 404}

        logger.info(f"Generating screenshot took: {time.time() - start_time} seconds")
        image = Image.open(destination_file)
        os.remove(destination_file)

        logger.info(f"Saving image to: {destination_file}")

        image.convert("RGB").save(destination_file, quality=100, dpi=(600, 600))
        os.chmod(destination_file, 0o777)

        logger.info(f"Image saved to: {destination_file}")
        logger.info(f"Rendering progress: {format(int(100 / pages * page))}%")
        # sys.stdout.write("\033[F")
        # sys.stdout.write("\033[K")
        page = page + 1
    render_driver.quit()
    logger.info(f"Rendering progress: 100%, finished in {time.time() - total_start_time} seconds")
    return create_response(
        create_destination_file_for_render(domain, uid),
        create_destination_file_for_render(domain, uid, None, False)
    )

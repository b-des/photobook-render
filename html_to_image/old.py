import os, shutil
import imgkit
from PIL import Image, ImageOps
import image_slicer
from domain_dict import domains
import sys

render_url = 'https://{}/index.php?route=photobook/photobook/renderPage&uid={}&page={}'
default_size = {'width': '2000', 'height': '1000'}
options = {
    'window-status': 'ready',
    'quiet': '',
    'quality': 100,
    'images': '',
    'zoom': 1,
    'format': 'jpg'
}


def create_destination_file_for_preview(domain, uid, filename=None, include_os_path=True):
    try:
        path = os.path.join(domains[domain] if include_os_path is True else domain, 'image/photobook/snapshots', uid)
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
        path = os.path.join(domains[domain] if include_os_path is True else domain, 'image/photobook/renders', uid)
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

    slice(original)
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
    #sys.stdout.write("\033[F")
    #sys.stdout.write("\033[K")


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
    '''
    Generate preview of book
    :param pages: number of pages
    :param uid: uid of book
    :param domain: site url, where book was created
    :param size: size of final image
    :param is_user_preview: indicate if it's user's book
    :return:
    '''
    if create_destination_file_for_preview(domain, uid) is None:
        return {'message': "Unregistered domain name received", 'code': 400}

    if size is None:
        size = default_size
    page = 1
    while page <= pages:

        if is_user_preview is False:
            destination = create_destination_file_for_preview(domain, uid, '{}-full'.format(page))
        else:
            destination = create_destination_file_for_preview(domain, '%s/%s' % (uid, 'preview'), page)

        url = render_url.format(domain, uid, page - 1)
        url = url + '&width={}&height={}'.format(size['width'], size['height'])

        options.update(size)
        print('Create request to {}'.format(url))
        imgkit.from_url(url, destination, options=options)
        try:
            imgkit.from_url(url, destination, options=options)
        except:
            return {'message': "Error occurred while render image with wkhtmltoimage", 'code': 404}

        image = Image.open(destination)
        image.save(destination, quality=100, dpi=(600, 600))
        os.chmod(destination, 0o777)
        # if rendering user's book
        # save it to preview dir without slicing
        if is_user_preview is False:
            slice_page(page, pages, domain, uid)

        page = page + 1

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
    if create_destination_file_for_preview(domain, uid) is None:
        return {'message': "Unregistered domain name received", 'code': 400}

    try:
        path = os.path.join(domains[domain], 'image/photobook/renders', uid)
    except KeyError:
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
    while page < pages:
        destination_file = create_destination_file_for_render(domain, uid, page)

        url = render_url.format(domain, uid, page)
        url = url + '&isFullRender=true&width={}&height={}'.format(size['width'] - border_offset * 2,
                                                                   size['height'] - border_offset)
        options.update(size)
        print('Make request to {}'.format(url))
        try:
            imgkit.from_url(url, destination_file, options=options)
        except:
            print(sys.exc_info()[0])
            return {'message': "Error occurred while render image with wkhtmltoimage", 'code': 404}

        image = Image.open(destination_file)
        os.remove(destination_file)
        image.save(destination_file, quality=100, dpi=(600, 600))
        os.chmod(destination_file, 0o777)
        print('Rendering progress: {}%'.format(int(100 / pages * page)))
        #sys.stdout.write("\033[F")
        #sys.stdout.write("\033[K")
        page = page + 1
    print('Rendering progress: {}%'.format(100))
    return create_response(
        create_destination_file_for_render(domain, uid),
        create_destination_file_for_render(domain, uid, None, False)
    )
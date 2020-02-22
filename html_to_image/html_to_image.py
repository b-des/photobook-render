import os
import imgkit
from PIL import Image, ImageOps
import image_slicer
from domain_dict import domains

render_url = 'https://{}/index.php?route=photobook/photobook/renderPage&uid={}&page={}'

options = {
    'window-status': 'ready',
    # 'quiet': '',
    'quality': 100,
    'format': 'jpg'
}


def destination_file(domain, uid, filename=None, include_os_path=True):
    try:
        path = os.path.join(domains[domain] if include_os_path is True else domain, 'photobook/snapshots', uid)
    except KeyError:
        return None

    if not os.path.exists(path):
        os.makedirs(path)
    if filename is None:
        return path
    return os.path.join(path, '{}.jpg'.format(filename))


def slice(path):
    img = Image.open(path)
    res = (img.crop((0, 0, 500, 500)), img.crop((500, 0, 1000, 500)))
    return res


def slice_page(page, pages, domain, uid):
    original = destination_file(domain, uid, '{}-full'.format(page))
    sliced = image_slicer.slice(original, 2, save=False)
    slice(original)
    if page == 1:
        sliced[0].image.save(destination_file(domain, uid, '{}-original'.format(pages * 2)))
        sliced[1].image.save(destination_file(domain, uid, '1-original'))

        # sliced[0].image.crop((10, 10, 500, 500 - 10)).save(destination_file(domain, uid, pages * 2), quality=100)
        # sliced[1].image.crop((10, 10, 500, 500 - 10)).save(destination_file(domain, uid, 1), quality=100)
        sliced[0].image.crop((10, 10, 500, 490)).save(destination_file(domain, uid, pages * 2), quality=100)
        sliced[1].image.crop((0, 10, 490, 490)).save(destination_file(domain, uid, 1), quality=100)
    else:
        number = page - 2 + page
        if number != 2:
            sliced[0].image.crop((10, 10, 500, 490)).save(destination_file(domain, uid, number), quality=100)
        else:
            sliced[0].image.save(destination_file(domain, uid, number), quality=100)

        if number + 1 != pages * 2 - 1:
            sliced[1].image.crop((0, 10, 490, 490)).save(destination_file(domain, uid, number + 1), quality=100)
        else:
            sliced[1].image.save(destination_file(domain, uid, number + 1), quality=100)

    os.remove(original)


def create_coverages(pages):
    images = [Image.open(x) for x in ['images/1.jpg', 'images/2.jpg',
                                      'images/{}.jpg'.format(pages * 2 - 1), 'images/{}.jpg'.format(pages * 2)]]
    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)
    max_height = max(heights)
    new_im = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]

    new_im.save('images/book-covers.jpg')


def create_borders(pages, domain, uid):
    # left canvas
    cover_right = Image.open(destination_file(domain, uid, '{}-original'.format(1)))
    left_image = Image.open(destination_file(domain, uid, 2))

    bottom_box = (0, cover_right.size[1] - 10, cover_right.size[0], cover_right.size[1])
    top_box = (0, 0, cover_right.size[0], 10)
    left_box = (cover_right.size[0] - 10, 0, cover_right.size[0], cover_right.size[1])

    bottom_region = ImageOps.flip(ImageOps.mirror(cover_right.crop(bottom_box)))
    top_region = ImageOps.flip(ImageOps.mirror(cover_right.crop(top_box)))
    left_region = cover_right.crop(left_box)

    left_image.paste(bottom_region, (0, left_image.size[1] - 10))
    left_image.paste(top_region, (0, 0))
    left_image.paste(left_region, (0, 0))

    left_image.save(destination_file(domain, uid, 2), quality=100)

    # right canvas
    cover_left = Image.open(destination_file(domain, uid, '{}-original'.format(pages * 2)))
    right_image = Image.open(destination_file(domain, uid, pages * 2 - 1))

    bottom_box = (0, cover_left.size[1] - 10, cover_left.size[0], cover_left.size[1])
    top_box = (0, 0, cover_left.size[0], 10)
    right_box = (0, 0, cover_left.size[0] - 10, cover_left.size[1])

    bottom_region = ImageOps.flip(ImageOps.mirror(cover_left.crop(bottom_box)))
    top_region = ImageOps.flip(ImageOps.mirror(cover_left.crop(top_box)))
    right_region = cover_left.crop(right_box)

    right_image.paste(bottom_region, (0, right_image.size[1] - 10))
    right_image.paste(top_region, (0, 0))
    right_image.paste(right_region, (right_image.size[0] - 10, 0))

    right_image.save(destination_file(domain, uid, pages * 2 - 1), quality=100)
    os.remove(destination_file(domain, uid, '{}-original'.format(1)))
    os.remove(destination_file(domain, uid, '{}-original'.format(pages * 2)))


def create_response(destination, url_path):
    f = []
    for (dirpath, dirnames, filenames) in os.walk(destination):
        [f.extend([os.path.join(url_path, file)]) for file in filenames]
        break
    return {'data': f, 'code': 200}


def make_previews(pages=0, uid='', domain='', size=None, is_user_preview=False):
    print("Is user preview:")
    print(is_user_preview)

    if destination_file(domain, uid) is None:
        return {'message': "Unregistered domain name received", 'code': 400}

    if size is None:
        size = {'width': '1000', 'height': '500'}
    page = 1
    while page <= pages:
        # if rendering user's book
        # save it to preview dir without slicing
        if is_user_preview is False:
            destination = destination_file(domain, uid, '{}-full'.format(page))
        else:
            destination = destination_file(domain, '%s/%s' % (uid, 'preview'), page)

        url = render_url.format(domain, uid, page)

        options.update(size)
        try:
            imgkit.from_url(url, destination, options=options)
        except:
            return {'message': "Error occurred while parse url", 'code': 404}

        if is_user_preview is False:
            slice_page(page, pages, domain, uid)

        page = page + 1

    # if is user's book render
    # don't create borders
    if is_user_preview is False:
        create_borders(pages, domain, uid)
        return create_response(
            destination_file(domain, uid),
            destination_file(domain, '%s/%s' % (uid, 'preview'), False)
        )
    else:
        return create_response(
            destination_file(domain, '%s/%s' % (uid, 'preview')),
            destination_file(domain, '%s/%s' % (uid, 'preview'), False)
        )

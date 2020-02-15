import os
import imgkit
from PIL import Image, ImageOps
import image_slicer
from domain_dict import domains

render_url = 'https://{}/index.php?route=photobook/photobook/renderPage&uid={}&page={}'

options = {
    'window-status': 'ready',
}


def destination_file(domain, uid, filename=None):
    try:
        path = os.path.join(domains[domain], 'photobook/snapshots', uid)
    except KeyError:
        return None

    if not os.path.exists(path):
        os.makedirs(path)
    if filename is None:
        return path
    return os.path.join(path, '{}.jpg'.format(filename))


def slice_page(page, pages, domain, uid):
    original = destination_file(domain, uid, '{}-full'.format(page))
    sliced = image_slicer.slice(original, 2, save=False)
    if page == 1:
        sliced[0].save(destination_file(domain, uid, pages * 2))
        sliced[1].save(destination_file(domain, uid, 1))
    else:
        number = page - 2 + page
        print(number)
        sliced[0].save(destination_file(domain, uid, number))
        print(number + 1)
        sliced[1].save(destination_file(domain, uid, number + 1))
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
    cover_right = Image.open(destination_file(domain, uid, 1))
    left_image = Image.open(destination_file(domain, uid, 2))

    bottom_box = (0, cover_right.size[1] - 10, cover_right.size[0], cover_right.size[1])
    top_box = (0, 0, cover_right.size[0], 10)
    left_box = (0, 0, 10, cover_right.size[1])

    bottom_region = ImageOps.flip(ImageOps.mirror(cover_right.crop(bottom_box)))
    top_region = ImageOps.flip(ImageOps.mirror(cover_right.crop(top_box)))
    left_region = cover_right.crop(left_box)

    left_image.paste(bottom_region, (0, left_image.size[1] - 10))
    left_image.paste(top_region, (0, 0))
    left_image.paste(left_region, (0, 0))

    left_image.save(destination_file(domain, uid, 2))

    # right canvas
    cover_left = Image.open(destination_file(domain, uid, pages * 2))
    right_image = Image.open(destination_file(domain, uid, pages * 2 - 1))

    bottom_box = (0, cover_left.size[1] - 10, cover_left.size[0], cover_left.size[1])
    top_box = (0, 0, cover_left.size[0], 10)
    right_box = (cover_left.size[0] - 10, 0, cover_left.size[0], cover_left.size[1])

    bottom_region = ImageOps.flip(ImageOps.mirror(cover_left.crop(bottom_box)))
    top_region = ImageOps.flip(ImageOps.mirror(cover_left.crop(top_box)))
    right_region = cover_left.crop(right_box)

    right_image.paste(bottom_region, (0, right_image.size[1] - 10))
    right_image.paste(top_region, (0, 0))
    right_image.paste(right_region, (right_image.size[0] - 10, 0))

    right_image.save(destination_file(domain, uid, pages * 2 - 1))


def create_response(destination):
    f = []
    for (dirpath, dirnames, filenames) in os.walk(destination):
        [f.extend([os.path.join(destination, file)]) for file in filenames]
        break
    return {'data': f, 'code': 200}


def make_previews(pages=0, uid='', domain='', size=None):

    if destination_file(domain, uid) is None:
        return {'message': "Unregistered domain name received", 'code': 400}

    if size is None:
        size = {'width': '1000', 'height': '500'}
    page = 1
    while page <= pages:
        destination = destination_file(domain, uid, '{}-full'.format(page))
        url = render_url.format(domain, uid, page)
        options.update(size)
        try:
            imgkit.from_url(url, destination, options=options)
        except:
            return {'message': "Error occurred while parse url", 'code': 404}

        slice_page(page, pages, domain, uid)
        page = page + 1

    create_borders(pages, domain, uid)
    return create_response(destination_file(domain, uid))
    # create_coverages()

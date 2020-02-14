import os
import imgkit
from PIL import Image, ImageOps
import image_slicer

url = 'https://{}/index.php?route=photobook/photobook/renderPage&uid={}&page={}'

options = {
    'window-status': 'ready',
    'width': '1000',
    'height': '500',
}
#1 - 10,1
#2 - 2,3
#3 - 4,5
#4 - 6,7
#5 - 8,9


def slice_page(page, pages):
    sliced = image_slicer.slice('images/{}.jpg'.format(page), 2, save=False)
    if page == 1:
        sliced[0].save("images/{}.jpg".format(pages*2))
        sliced[1].save("images/{}.jpg".format(1))
    else:
        number = page - 2 + page
        sliced[0].save("images/{}.jpg".format(number))
        sliced[1].save("images/{}.jpg".format(number + 1))


def create_coverages(pages):
    images = [Image.open(x) for x in ['images/1.jpg', 'images/2.jpg',
                                      'images/{}.jpg'.format(pages*2-1), 'images/{}.jpg'.format(pages*2)]]
    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)
    max_height = max(heights)
    new_im = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]

    new_im.save('images/book-covers.jpg')


def create_borders(pages):
    # left canvas
    cover_right = Image.open('images/1.jpg')
    left_image = Image.open('images/2.jpg')

    bottom_box = (0, cover_right.size[1] - 10, cover_right.size[0], cover_right.size[1])
    top_box = (0, 0, cover_right.size[0], 10)
    left_box = (0, 0, 10, cover_right.size[1])

    bottom_region = ImageOps.flip(ImageOps.mirror(cover_right.crop(bottom_box)))
    top_region = ImageOps.flip(ImageOps.mirror(cover_right.crop(top_box)))
    left_region = cover_right.crop(left_box)

    left_image.paste(bottom_region, (0, left_image.size[1] - 10))
    left_image.paste(top_region, (0, 0))
    left_image.paste(left_region, (0, 0))

    left_image.save("images/2.jpg")

    # right canvas
    cover_left = Image.open('images/{}.jpg'.format(pages * 2))
    right_image = Image.open('images/{}.jpg'.format(pages * 2 - 1))

    bottom_box = (0, cover_left.size[1] - 10, cover_left.size[0], cover_left.size[1])
    top_box = (0, 0, cover_left.size[0], 10)
    right_box = (cover_left.size[0] - 10, 0,  cover_left.size[0], cover_left.size[1])

    bottom_region = ImageOps.flip(ImageOps.mirror(cover_left.crop(bottom_box)))
    top_region = ImageOps.flip(ImageOps.mirror(cover_left.crop(top_box)))
    right_region = cover_left.crop(right_box)

    right_image.paste(bottom_region, (0, right_image.size[1] - 10))
    right_image.paste(top_region, (0, 0))
    right_image.paste(right_region, (right_image.size[0] - 10, 0))

    right_image.save('images/{}.jpg'.format(pages * 2 - 1))


def make_previews(pages=0, uid='ojlzBWuRicYHXzG2', domain='pechat.photo', dest=''):
    page = 1
    while page <= pages:
        imgkit.from_url(url.format(domain, uid, page), os.path.join(dest, '{}.jpg'.format(page)), options=options)
        slice_page(page, pages)
        page = page + 1

    create_borders(pages)
    #create_coverages()

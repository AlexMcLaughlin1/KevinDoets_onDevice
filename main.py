#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import sys
import time
import logging

from PIL import Image

HERE = os.path.dirname(os.path.realpath(__file__))
LIBDIR_CANDIDATES = [
    os.path.join(HERE, 'lib'),
    os.path.join(os.path.dirname(os.path.dirname(HERE)), 'lib'),
]
for libdir in LIBDIR_CANDIDATES:
    if os.path.exists(libdir):
        sys.path.append(libdir)
        break

from waveshare_epd import epd5in83_V2

IMAGE_NAME = 'departures_qrp.png'


def _load_image(path):
    img = Image.open(path)
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        return background
    return img.convert('RGB')


def _choose_target_size(epd, img):
    img_ratio = img.width / img.height
    horiz = (epd.height, epd.width)
    vert = (epd.width, epd.height)
    horiz_ratio = horiz[0] / horiz[1]
    vert_ratio = vert[0] / vert[1]
    if abs(img_ratio - horiz_ratio) <= abs(img_ratio - vert_ratio):
        return horiz
    return vert


def _letterbox(img, size):
    target_w, target_h = size
    resample = Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS
    img_copy = img.copy()
    img_copy.thumbnail((target_w, target_h), resample)
    canvas = Image.new('RGB', size, (255, 255, 255))
    left = (target_w - img_copy.width) // 2
    top = (target_h - img_copy.height) // 2
    canvas.paste(img_copy, (left, top))
    return canvas


def _to_epd_bw(img, size):
    img = _letterbox(img, size)
    return img.convert('1')


def main():
    logging.basicConfig(level=logging.INFO)

    image_path = os.path.join(HERE, IMAGE_NAME)
    if not os.path.exists(image_path):
        raise FileNotFoundError('PNG not found: %s' % image_path)

    logging.info('init and clear')
    epd = epd5in83_V2.EPD()
    epd.init()
    epd.Clear()
    time.sleep(1)

    img = _load_image(image_path)
    target_size = _choose_target_size(epd, img)
    bw_image = _to_epd_bw(img, target_size)

    logging.info('displaying %s', IMAGE_NAME)
    epd.display(epd.getbuffer(bw_image))
    time.sleep(2)

    logging.info('sleep')
    epd.sleep()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        logging.exception('failed')
        try:
            epd5in83_V2.epdconfig.module_exit(cleanup=True)
        except Exception:
            pass
        raise

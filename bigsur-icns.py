#!/usr/bin/env python3
# coding: utf8
import typing
import argparse
import functools
import os
import re
import shutil
import sys
import subprocess as P
import os.path as path


# The background image is of size 1024x1024, the transparent margin on each
# edge is 100px.
BG_IMG = path.join(path.dirname(__file__), "white_bg_1024x1024.png")
BG_WIDTH = 1024
BG_MARGIN = 100
BG_MARGIN_RATIO = 2 * BG_MARGIN / BG_WIDTH

# Original icon png file name
ORIG_PNG_NAME = "icon_512x512.png"


def gm_cmd(cmd: str, debug: bool = False) -> str:
    """
    GraphicsMagick CLI wrapper
    """
    full_cmd = "gm {}".format(cmd)
    if debug:
        print(full_cmd)
    with os.popen(full_cmd) as f:
        return f.read()


def get_width(filename: str) -> int:
    return parse_width(gm_cmd("identify {}".format(filename)))


def parse_width(s: str) -> int:
    m = re.search(r"(\d+)x(\d+)", s)
    if m is None:
        raise Exception("Unknown dimension string")
    return int(m.group(1))


def overlay(size: int, fg_img: str, output_dir: str, scale: int = 1, delta_x: int = 0, delta_y: int = 0, bg_img: str = BG_IMG) -> str:
    inner_size = int(size * (1 - BG_MARGIN_RATIO) * scale)
    offset = int((size - inner_size) / 2)
    gm_cmd("composite -resize {inner_size}x{inner_size} -geometry +{offset_x}+{offset_y} '{icon}' \
                      -resize {outer_size}x{outer_size} '{background}' '{output}'".format(
        inner_size=inner_size,
        outer_size=size,
        offset_x=offset+delta_x,
        offset_y=offset+delta_y,
        icon=fg_img,
        background=bg_img,
        output=path.join(output_dir, "icon_{0}x{0}.png".format(size))
    ))
    return path.join(output_dir, "icon_{0}x{0}.png".format(size))


def resize(size: int, img: str, output_dir: str) -> None:
    new_name = path.join(output_dir, "icon_{0}x{0}.png".format(size))
    gm_cmd("convert -resize {size}x{size} '{img}' '{new_name}'".format(
        size=size, img=img, new_name=new_name))


def convert_icns_to_iconset(icns_file: str) -> str:
    """
    the `.iconset` file is a folder with PNG images of different size
    """
    output_path = path.abspath(path.basename(icns_file).replace(".icns", ".iconset"))
    __ensure_path_not_exist(output_path)
    c = P.call("iconutil -c iconset -o '{}' '{}'".format(output_path, icns_file), shell=True)
    if c != 0:
        raise Exception("Failed to convert icns")
    return output_path


def convert_iconset_to_icns(iconset_file: str) -> str:
    output_path = path.abspath(iconset_file.replace(".iconset", ".icns"))
    __ensure_path_not_exist(output_path)
    c = P.call("iconutil -c icns -o '{}' '{}'".format(output_path, iconset_file), shell=True)
    if c != 0:
        raise Exception("Failed to convert iconset")
    return output_path


def __ensure_path_not_exist(p: str) -> None:
    if path.exists(p):
        raise Exception("Path {} will be overriden".format(p))


def process(iconset_dir: str, output_dir: str) -> None:
    guess_best_size = None
    for s in [512, 256, 128]:
        if path.exists(path.join(iconset_dir, "icon_{0}x{0}.png".format(s))):
            guess_best_size = s
            break
    if guess_best_size is None:
        raise Exception("The icns doesn't contain icon image with good resolution")
    orig_img = path.join(iconset_dir, "icon_{0}x{0}.png".format(guess_best_size))
    img = overlay(guess_best_size, orig_img, output_dir, scale=0.8)
    for s in [16, 32, 128, 256]:
        if s < guess_best_size:
            resize(s, img, output_dir)


def parse_args():
    p = argparse.ArgumentParser("BigSur icon converter")
    p.add_argument("file", metavar="FILE", type=str)
    p.add_argument("-x", help="x offset", type=int, default=0)
    p.add_argument("-y", help="y offset", type=int, default=0)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    iconset_dir = convert_icns_to_iconset(args.file)
    output_dir = os.path.abspath("new-" + path.basename(iconset_dir))
    os.mkdir(output_dir)
    try:
        process(iconset_dir, output_dir)
        convert_iconset_to_icns(output_dir)
    except Exception as e:
        print(e)
    finally:
        shutil.rmtree(output_dir)
        shutil.rmtree(iconset_dir)

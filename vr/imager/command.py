#!/usr/bin/env python

import pkg_resources

import yaml
from jaraco.ui import cmdline

from vr.imager.build import run_image
from vr.common.models import ConfigData


def get_version():
    try:
        return pkg_resources.get_distribution('vr.imager').version
    except Exception:
        return None


class Image:
    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument(
            'image_data', help="Path to image.yaml file.",
            type=ImageData.from_filename, metavar='file')
        parser.add_argument(
            '--version', action='version', version=get_version())


class Build(Image, cmdline.Command):
    @classmethod
    def run(cls, args):
        run_image(args.image_data, make_tarball=True)


class Shell(Image, cmdline.Command):
    @classmethod
    def run(cls, args):
        run_image(args.image_data, cmd='/bin/bash', make_tarball=False)


class ImageData(ConfigData):
    _required = [
        'base_image_url',
        'base_image_name',
        'new_image_name',
        'script_url',
    ]

    _optional = [
        'base_image_md5',
        'new_image_md5',
        'env',
    ]

    def __repr__(self):
        print('<ImageData: %s+%s>' % (self.base_image_name, self.script_url))

    @classmethod
    def from_filename(cls, filename):
        with open(filename, 'rb') as f:
            return cls(yaml.safe_load(f))


invoke = cmdline.Command.invoke

from __future__ import print_function, unicode_literals

import os
import pkg_resources
import shutil
import subprocess
import sys
import tarfile

import path

from vr.common.utils import tmpdir, get_lxc_version, get_lxc_network_config
from vr.runners.image import ensure_image, IMAGES_ROOT
from vr.runners.base import ensure_file


def run_image(*args, **kwargs):
    outfolder = path.Path.getcwd()
    with tmpdir():
        _run_image(outfolder, *args, **kwargs)


def _run_image(outfolder, image_data, cmd=None, user='root',
        make_tarball=False):
    # download image
    image_path = path.Path('img').realpath()
    print("Ensuring presence of " + image_data.base_image_url)
    ensure_image(
        image_data.base_image_name,
        image_data.base_image_url,
        IMAGES_ROOT,
        image_data.base_image_md5,
        untar_to=image_path,
    )

    # write LXC config file
    tmpl = get_template('base_image.lxc')
    content = tmpl % {
        'image_path': image_path,
        'network_config': get_lxc_network_config(get_lxc_version()),
    }
    lxc_file_path = path.Path.getcwd() / 'imager.lxc'
    print("Writing %s" % lxc_file_path)
    lxc_file_path.write_text(content, encoding='ascii')

    lxc_name = 'build_image-' + image_data.new_image_name

    script_path = None
    if cmd is None:
        # copy bootstrap script into place and ensure it's executable.
        script = os.path.basename(image_data.script_url)
        script_path = image_path / script
        if os.path.exists(image_data.script_url):
            shutil.copy(image_data.script_url, script_path)
        else:
            ensure_file(image_data.script_url, script_path)
        script_path.chmod('a+x')
        real_cmd = '/' + script
    else:
        real_cmd = cmd

    # Call lxc-start, passing in our LXC config file and telling it to run
    # our build script inside the container.
    lxc_args = [
        'lxc-start',
        '--name', lxc_name,
        '--rcfile', lxc_file_path,
        '--',
        real_cmd,
    ]
    path_items = (
        '/usr/local/sbin',
        '/usr/local/bin',
        '/usr/sbin',
        '/usr/bin',
        '/sbin',
        '/bin',
        '/usr/games',
    )
    env = {
        'PATH': os.pathsep.join(path_items),
        'HOME': '/root',
    }
    env.update(image_data.env or {})
    if 'TERM' in os.environ:
        env['TERM'] = os.environ['TERM']

    logpath = os.path.join(outfolder, '%s.log' % image_data.new_image_name)
    print("LOGPATH", logpath)
    with open(logpath, 'w') as logfile:
        tee(lxc_args, env, logfile)

    # remove build script if we used one.
    if cmd is not None:
        os.remove(script_path)

    if make_tarball:
        img_name = '{image_data.new_image_name}.tar.gz'.format(**locals())
        tardest = os.path.join(outfolder, img_name)
        print("Compressing image to " + tardest)
        with tarfile.open(tardest, 'w:gz') as tar:
            tar.add(image_path, arcname='')


def tee(command, env, outfile):
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    lines = []
    status_code = None
    print("run:", command)

    def handle_output(content):
        outfile.write(content)
        sys.stdout.write(content)
        lines.append(content)

    while status_code is None:
        status_code = p.poll()
        handle_output(p.stdout.readline())

    # capture any last output.
    handle_output(p.stdout.read())

    if status_code != 0:
        raise subprocess.CalledProcessError(
            status_code,
            command,
            output=''.join(lines),
        )


def get_template(name):
    """
    Look for 'name' in the vr.runners.templates folder.  Return its contents.

    >>> import six
    >>> tmpl = get_template('base_image.lxc')
    >>> isinstance(tmpl, six.string_types)
    True
    """
    path = 'templates/' + name
    b_stream = pkg_resources.resource_stream('vr.imager', path)
    return b_stream.read().decode('utf-8')

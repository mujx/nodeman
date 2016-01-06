
""" Helper functions for the CLI. """

import functools
import os
import platform

import requests
import semver
from bs4 import BeautifulSoup

from nodeman.config import DIST_URL, STORAGE


def installed_versions():
    """
    Find the versions installed by nodeman.
    """
    versions = [version for version in os.listdir(STORAGE)]
    versions = sorted(versions, key=functools.cmp_to_key(semver.compare))

    return versions


def installed_packages(versions=installed_versions()):
    """
    Finds all globally installed packages
    """
    bins = set()
    for directory in os.listdir(STORAGE):
        if directory in versions:
            for b in os.listdir(STORAGE + '/' + directory + '/bin/'):
                if b != 'npm' and b != 'node' and not b.startswith('_'):
                    bins.add(b)
    return bins


def extract_link(version):
    """
    Get the download link for a Node.js version.
    """
    if version == 'latest':
        url = DIST_URL + version + '/'
    else:
        semver.parse(version)
        url = DIST_URL + 'v' + version + '/'

    system, arch = get_system_info().split('-')
    content = BeautifulSoup(requests.get(url).content, 'html.parser')

    for a in content.find_all('a'):
        link = a['href']
        if link.startswith('node-') and link.endswith('.tar.gz'):
            if system in link and arch in link:
                version = link.split('-')[1].split('v')[1]
                break

    return (url + link, version,)


def get_system_info():
    bits, _ = platform.architecture()
    system = platform.system()
    machine = platform.machine()

    if machine.lower().startswith('arm'):
        return 'linux-' + machine.lower()

    if bits.startswith('32'):
        arch = 'x86'
    elif bits.startswith('64'):
        arch = 'x64'
    else:
        raise OSError

    return system.lower() + '-' + arch


def get_shell_config():
    config = os.path.expanduser('~/.bashrc')

    if os.environ['SHELL'].endswith('zsh'):
        config = os.path.expanduser('~/.zshrc')
    elif os.environ['SHELL'].endswith('bash'):
        config = os.path.expanduser('~/.bashrc')

    return config


def append_to_path(version):

    config = get_shell_config()

    print(':: updating', config)

    nodeman_export = 'export PATH=' + STORAGE + '/'
    with open(config, 'r') as f:
        content = f.read().rstrip().split('\n')

        for i, line in enumerate(content):
            if nodeman_export in line:
                del content[i]

        cmd = nodeman_export + version + '/bin:$PATH'
        content.append(cmd)

    with open(config, 'w') as f:
        f.write('\n'.join(content))
        f.write('\n')

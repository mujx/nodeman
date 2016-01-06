
""" Helper functions for the CLI. """

import functools
import os
import platform

import requests
import semver
from bs4 import BeautifulSoup

from nodeman.config import DIST_URL, STORAGE

NODEMAN_EXPORT = 'export PATH=' + STORAGE + '/'


def installed_versions():
    """
    Find the versions installed by nodeman.
    """
    versions = [version for version in os.listdir(STORAGE)]
    versions = sorted(versions, key=functools.cmp_to_key(semver.compare))

    return versions


def get_current_version():
    candidates = []
    config = get_shell_config()

    with open(config, 'r') as f:
        content = f.read().rstrip().split('\n')
        for line in content:
            if NODEMAN_EXPORT in line:
                candidates.append(extract_version(line))
    if candidates:
        return candidates[-1]
    else:
        return candidates


def extract_version(export):
    return export.split('/')[-2]


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


def search_upstream(query):
    available = []
    content = BeautifulSoup(requests.get(DIST_URL).content, 'html.parser')

    for a in content.find_all('a'):
        link = a['href']
        if link.startswith('v' + query):
            available.append(link.split('/')[0].split('v')[1])

    return sorted(available, key=functools.cmp_to_key(semver.compare))


def append_to_path(version):

    config = get_shell_config()

    print(':: updating', config)

    NODEMAN_EXPORT = 'export PATH=' + STORAGE + '/'
    with open(config, 'r') as f:
        content = f.read().rstrip().split('\n')

        for i, line in enumerate(content):
            if NODEMAN_EXPORT in line:
                del content[i]

        cmd = NODEMAN_EXPORT + version + '/bin:$PATH'
        content.append(cmd)

    with open(config, 'w') as f:
        f.write('\n'.join(content))
        f.write('\n')

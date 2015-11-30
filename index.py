import sys
import platform
import functools
import os
import tarfile
import shutil

from subprocess import call
from pkg_resources import require
from string import Template

import requests
import click
import semver

from bs4 import BeautifulSoup

TEMP_STORAGE = '/tmp/node-versions/'
STORAGE = os.path.expanduser('~') + '/.node-versions'
TARFILE = Template(TEMP_STORAGE + 'node-v$version.tar.gz')

if not os.path.exists(STORAGE):
    try:
        os.mkdir(STORAGE)
    except OSError as e:
        print(e)


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Return the current version.')
def cli(version):
    """ CLI tool to manage Node.js binaries """

    if version:
        print(require('nodeman')[0].version)


@cli.command()
@click.pass_context
def latest(ctx):
    """
    Install the latest version
    """
    link, version = extract_link('latest')
    ctx.invoke(install, version=version, link=link, from_ctx=True)


@cli.command()
def ls():
    """
    Show all the available versions
    """
    for version in installed_versions():
        print(version)


def installed_versions():
    versions = [version for version in os.listdir(STORAGE)]
    versions = sorted(versions, key=functools.cmp_to_key(semver.compare))

    return versions


@cli.command()
def sync():
    """
    Sync globally installed packages among versions
    """
    pkgs = installed_packages()

    for version in installed_versions():
        print(':: installing for', version)
        diff = pkgs.difference(installed_packages(versions=[version]))
        for pkg in diff:
            print('=>', pkg)
            path = STORAGE + '/' + version + '/bin/'
            call([path + 'npm', 'i', '-g', pkg])


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
    DIST_URL = 'https://nodejs.org/dist/'

    if version == 'latest':
        DIST_URL += version + '/'
    else:
        semver.parse(version)
        DIST_URL += 'v' + version + '/'

    system, arch, _ = get_system_info()
    content = BeautifulSoup(requests.get(DIST_URL).content, 'html.parser')

    for a in content.find_all('a'):
        link = a['href']
        if link.startswith('node-') and link.endswith('.tar.gz'):
            if system in link and arch in link:
                version = link.split('-')[1].split('v')[1]
                break

    return (DIST_URL + link, version,)


def get_system_info():
    bits, _ = platform.architecture()
    system = platform.system()
    config = os.path.expanduser('~/.bashrc')

    if os.environ['SHELL'].endswith('zsh'):
        config = os.path.expanduser('~/.zshrc')
    elif os.environ['SHELL'].endswith('bash'):
        config = os.path.expanduser('~/.bashrc')

    if bits.startswith('32'):
        arch = 'x86'
    elif bits.startswith('64'):
        arch = 'x64'
    else:
        raise OSError

    return (system.lower(), arch, config,)


@cli.command()
@click.argument('version')
def rm(version):
    """
    Remove a version
    """
    semver.parse(version)

    if not os.path.exists(STORAGE + '/' + version):
        print(':: %s is not installed' % version)
        return

    print(':: deleting binary...')
    shutil.rmtree(STORAGE + '/' + version)

    _, _, config = get_system_info()

    content = []
    with open(config, 'r') as f:
        content = f.read().split('\n')

        for i, line in enumerate(content):
            if STORAGE + '/' + version in line:
                print(':: cleaning up', config)
                del content[i]

    with open(config, 'w') as f:
        f.write('\n'.join(content))


@cli.command()
@click.argument('version')
def install(version, link='', from_ctx=False):
    """
    Install a version
    """
    if version is not 'latest':
        semver.parse(version)

    if not os.path.exists(STORAGE):
        try:
            os.mkdir(STORAGE)
        except OSError as e:
            raise e

    if os.path.exists(STORAGE + '/' + version):
        print(':: %s is already installed' % version)
        return

    if not from_ctx:
        link, version = extract_link(version)

    print(':: downloading...v%s' % version)
    res = requests.get(link)

    if res.status_code == 404:
        print(version, 'not found')
        sys.exit(1)

    if not os.path.exists(TEMP_STORAGE):
        try:
            os.mkdir(TEMP_STORAGE)
        except OSError as e:
            raise e

    tarball = TARFILE.substitute(version=version)

    with open(tarball, 'wb') as f:
        f.write(res.content)

    print(':: extracting tarball')

    with tarfile.open(tarball, 'r:gz') as f:
        f.extractall(path=STORAGE)

    system, arch, _ = get_system_info()
    os.rename(STORAGE + '/' + 'node-v' + version + '-' + system + '-' + arch,
              STORAGE + '/' + version)

    print(':: installing...')

    append_to_path(version)


def append_to_path(version):

    _, _, config = get_system_info()

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


@cli.command()
@click.argument('version')
def use(version):
    """
    Switch to a different version
    """
    semver.parse(version)

    if not os.path.exists(STORAGE + '/' + version):
        print(':: version', version, 'is not installed.')
        sys.exit(1)

    append_to_path(version)


@cli.command()
def clean():
    """
    Remove all the installed versions
    """
    shutil.rmtree(STORAGE)
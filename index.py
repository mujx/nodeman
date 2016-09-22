import os
import codecs
import shutil
import sys
import tarfile
from subprocess import call

import click
import requests
import semver
from pkg_resources import require

from nodeman.config import STORAGE, TARFILE, TEMP_STORAGE

if not os.path.exists(STORAGE):
    try:
        os.mkdir(STORAGE)
    except OSError as e:
        print(e)

import nodeman.utils as utils


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Return the current version.')
def cli(version):
    """ CLI tool to manage Node.js binaries """

    if version:
        print(require('nodeman')[0].version)


@cli.command()
@click.pass_context
@click.option('-b', '--branch', help='The release branch to use')
def latest(ctx, branch):
    """
    Install the latest version
    """
    if branch is None:
        current = utils.get_current_version()
        if current:
            branch = current.split('.')[0]
        else:
            print(':: No version is installed')
            return

    latest = utils.search_upstream(branch)[-1]
    link, version = utils.extract_link(latest)
    ctx.invoke(install, version=version, link=link, from_ctx=True)


@cli.command()
def current():
    """
    Show the version in usage
    """
    current = utils.get_current_version()

    if not current:
        print(':: There is no active version')
    else:
        print(current)


@cli.command()
def ls():
    """
    Show all the available versions
    """
    for version in utils.installed_versions():
        print(version)


@cli.command()
def sync():
    """
    Sync globally installed packages among versions
    """
    pkgs = utils.installed_packages()

    for version in utils.installed_versions():
        diff = pkgs.difference(utils.installed_packages(versions=[version]))
        if diff:
            print(':: installing for v%s' % version)
        for pkg in diff:
            print('=> %s' % pkg)
            path = STORAGE + '/' + version + '/bin/'
            call([path + 'npm', 'i', '-g', pkg])


@cli.command()
@click.argument('version')
def rm(version):
    """
    Remove a version
    """
    semver.parse(version)

    if not os.path.exists(STORAGE + '/' + version):
        print(':: v%s is not installed' % version)
        return

    print(':: deleting binary...')
    shutil.rmtree(STORAGE + '/' + version)

    config = utils.get_shell_config()

    content = []
    with codecs.open(config, 'r', 'utf-8') as f:
        content = f.read().split('\n')

        for i, line in enumerate(content):
            if STORAGE + '/' + version in line:
                print(':: cleaning up %s' % config)
                del content[i]

    with codecs.open(config, 'w', 'utf-8') as f:
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
        print(':: v%s is already installed' % version)
        return

    if not from_ctx:
        link, version = utils.extract_link(version)

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

    system = utils.get_system_info()
    os.rename(STORAGE + '/' + 'node-v' + version + '-' + system,
              STORAGE + '/' + version)

    print(':: installing...')

    utils.append_to_path(version)


@cli.command()
@click.argument('version')
def use(version):
    """
    Switch to a different version
    """
    semver.parse(version)

    if not os.path.exists(STORAGE + '/' + version):
        print(':: v%s is not installed.' % version)
        sys.exit(1)

    utils.append_to_path(version)


@cli.command()
@click.argument('query')
def search(query):
    """
    Search upstream for available versions
    """
    for v in utils.search_upstream(query):
        print(v)


@cli.command()
@click.pass_context
def clean(ctx):
    """
    Remove all the installed versions
    """
    ctx.invoke(rm, version=utils.get_current_version())
    shutil.rmtree(STORAGE)

import os
from string import Template

TEMP_STORAGE = '/tmp/node-versions/'

STORAGE = os.path.expanduser('~') + '/.node-versions'

TARFILE = Template(TEMP_STORAGE + 'node-v$version.tar.gz')

DIST_URL = 'https://nodejs.org/dist/'


from setuptools import setup


setup(name='nodeman',
      version='0.5.4',
      packages=['nodeman'],
      py_modules=['index'],
      description='CLI tool to manage Node.js binaries',
      author='mujx',
      author_email='siderisk@auth.gr',
      url='https://github.com/mujx/nodeman',
      license='MIT',
      install_requires=[
          'Click == 5.*',
          'semver == 2.*',
          'BeautifulSoup4 == 4.*',
          'requests == 2.*'
          ],
      entry_points='''
        [console_scripts]
        nodeman=index:cli
      ''',
      )

nodeman  [![PyPI version](https://badge.fury.io/py/nodeman.svg)](https://badge.fury.io/py/nodeman)
----

#### Installation

```bash
pip install nodeman
```
#### Usage

```
$ nodeman --help

Usage: nodeman [OPTIONS] COMMAND [ARGS]...

  CLI tool to manage Node.js binaries

Options:
  --version  Return the current version.
  --help     Show this message and exit.

Commands:
  clean    Remove all the installed versions
  current  Show the version in usage
  install  Install a version
  latest   Install the latest version
  ls       Show all the available versions
  rm       Remove a version
  search   Search upstream for available versions
  sync     Sync globally installed packages among versions
  use      Switch to a different version
```

Installing v4.2.2

```bash
nodeman install 4.2.2
```

Switching versions

```bash
$ nodeman ls
4.2.2
5.1.0

$ nodeman use 5.1.0
```

Searching

```bash
$ nodeman search 5.1
5.1.0
5.1.1
```

Install the latest stable version

```bash
$ nodeman latest --branch 5
```

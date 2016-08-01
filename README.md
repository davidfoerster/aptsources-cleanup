## Purpose

Detects and interactively deactivates duplicate Apt source entries in
`/etc/sources.list` and `/etc/sources.list.d/*.list`.


## Prerequisites

  * Python 3.2+ (or Python 2.6+ if you really can't use Python 3)

  * The `aptsources` module. In Debian-based distribution you can find it in
    the `python3-apt` package (or `python-apt` if you only have Python 2).

    If you don't have it yet you can install it with:

       sudo apt-get install python3-apt


## Usage

    sudo ./apt-remove-duplicate-source-entries.py
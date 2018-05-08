## Purpose

Detects and interactively deactivates duplicate Apt source entries and
deletes sources list files without valid enabled source entries in
`/etc/sources.list` and `/etc/sources.list.d/*.list`.


## Prerequisites

  * Python 3.2+ (or Python 2.7+ if you really can't use Python 3)

  * The `aptsources` module. In Debian-based distribution you can find it in
    the `python3-apt` package (or `python-apt` if you only have Python 2).

    If you don't have it yet you can install it with:

        sudo apt-get install python3-apt


## Download

You can download a pre-bundled ZIP file executable by your Python interpreter:

  * [Latest Release](https://github.com/davidfoerster/aptsources-cleanup/releases/latest)
  * [All Releases](https://github.com/davidfoerster/aptsources-cleanup/releases)

Or you can download the source code and run it in Python albeit without translations.


## Usage

  * From a ZIP bundle:

        sudo python3 aptsources-cleanup.zip

  * From source code:

        sudo ./aptsources-cleanup

For a (slightly more) detailed description and individual command-line options
see the output of

    python3 aptsources-cleanup.zip --help

or

    ./aptsources-cleanup --help

depending on the deployment type.

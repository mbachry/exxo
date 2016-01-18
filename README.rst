====
exxo
====

**Only Linux x86_64 supported for now**

Build your Python package into a portable one-file binary and deploy
it just by copying it to target machine. The binary links to libc only
and doesn't require Python to be installed on the machine. Exxo was
created with DevOps professionals in mind, but the target audience may
become larger as project matures.

Exxo uses the excellent `PyRun`_ project and `zipapp`_ library. The
target binary is simply a pyrun binary with zipped application
concatenated at the end. This simple design was chosen in hope it
proves to be the most portable one (PyRun already works on most major
platforms). There's also an assumption that over time zipapps become
more popular and more essential packages will become zip safe.

In order for exxo to be practical, PyRun and CPython were patched in
the following ways:

* zipimport supports loading C extensions (otherwise too many pip
  libraries would be useless)

* zipimport is capable of loading code from ``__pycache__`` if Python
  3 is used

* original PyRun comes with few C modules distributed separately (with
  notable examples for multiprocessing or ctypes); exxo's PyRun on the
  other hand is a truly one file binary with all modules included (at
  the cost of portability loss, for now)

* all libraries standard Python extensions depend on (like sqlite3 or
  ncurses) are statically compiled in (again, it makes PyRun Linux
  only)

* few I/O functions in CPython are patched to make most zip unsafe
  packages work out of the box (read `Zip safety hacks`_ section
  below)

.. _PyRun: https://www.egenix.com/products/python/PyRun/
.. _zipapp: https://docs.python.org/3/library/zipapp.html

Download
--------

Exxo is self-hosting. You can download it `here`_. The archive
contains just one file: exxo binary you should put somewhere in your
``PATH``.

.. _here: https://bintray.com/artifact/download/mbachry/exxo/exxo-0.0.4.tar.xz

Quick start
-----------

Your package needs to have a working ``setup.py`` script. We'll use a
sample project from ``example`` directory in `exxo git
repository`_. It's a simple Flask application that prints connecting
IP address. It demonstrates using a C extension (gevent), handling
data files (Flask templates and static assets) and embedding gunicorn
- all in one portable binary.

Create a new virtualenv and activate it with::

    exxo venv /tmp/myenv
    . /tmp/myenv/bin/activate

The default Python version is 3.4. Use ``exxo venv -p 2.7`` for Python
2.7.

You can use the virtualenv in regular way. To build the target binary::

    cd example
    exxo build

You'll find the binary under ``dist`` directory. Go on and copy it to
some server and see if it works.

If you have upx installed (``apt-get install upx`` or ``dnf install
upx``) you can use ``-c`` flag (``exxo build -c``) to compress PyRun
binary and save some space.

.. _exxo git repository: https://github.com/mbachry/exxo/

Differences with similar projects
---------------------------------

There's already a significant competition for exxo, including
prominent projects like `pex`_ or `PyInstaller`_. Here are few things
I'd like to see exxo doing differently:

* single binary

* the binary should be almost 100% standalone (i.e. Python doesn't
  have to be preinstalled)

* good startup performance so that exxo can be used for small, short
  lived apps (this means not unpacking everything to temporary
  locations)

* user-friendliness: should stick to familiar solutions like virtualenv
  or setuptools

* should support at least most popular packages out of the box without
  manual tweaks at user side

* investment in zipapps - even if they need special attention today,
  they are the cleanest and most modern way of bundling Python apps

.. _pex: https://pex.readthedocs.org/en/stable/
.. _PyInstaller: http://www.pyinstaller.org/

Caveats
-------

Although exxo binary itself is statically linked, included C
extensions (if any) are not. All required shared libraries must be
installed on the target machine. For example, if you use ``lxml``, you
must install ``libxml2``. This shortcoming may be fixed in the future.

Also, exxo still links dynamically glibc for practical reasons
(nsswitch support, etc.). Although glibc uses ELF symbol versioning,
you shouldn't build your project on a machine with much newer version
of glibc than installed on destination server. Exxo release itself is
built on Ubuntu 10.04 (with openssl 1.0+) to make sure it runs on
every distro, including Centos 6.

Because your application is run as zipapp, it should be zip safe. This
applies to all dependencies too, although exxo is armed in few hacks
to make many third-party packages run out of the box (see `Zip safety
hacks`_ section below). The main violation against zip safety is using
filesystem API to read data files from inside your package. Don't do
this::

    open(os.path.join(os.path.dirname(__file__), 'index.html'))

Instead use `pkgutil`_ module and its ``get_data`` function::

    pkgutil.get_data('mypackage', 'index.html')

or `pkg_resources`_ module from ``setuptools`` for more sophisticated
API.

Note that your ``setup.py`` must have one (and exactly one)
``console_scripts`` entry point defined for ``exxo build`` to work
correctly.

Although exxo tries hard to load everything directly from an
executable, some resources still have to be unzipped to a temporary
directory due to OS limitations. This applies mostly to bundled
binaries (C extensions, shared libraries for ``ctypes``, ELF
binaries), as it's nearly impossible to ``dlopen`` directly from a
zip. One serious limitation coming from this behaviour is that an exxo
binary won't work, if your ``/tmp`` directory happens to be mounted with
``-o noexec``.

.. _pkgutil: https://docs.python.org/3/library/pkgutil.html
.. _pkg_resources: https://pythonhosted.org/setuptools/pkg_resources.html
.. _example/myip/myip.py: https://github.com/mbachry/exxo/blob/master/example/myip/myip.py

Zip safety hacks
----------------

Exxo implements few patches over CPython to improve zip compatibility
out of the box.

Many popular Python packages are zip unsafe (including
Django). Luckily most of zip unsafe code follows the same pattern of
loading bundled resources mentioned in previous section::

    open(os.path.join(os.path.dirname(__file__), 'templates', 'index.html'))

If loaded from an unpatched exxo binary, it will fail with an
exception like::

    NotADirectoryError: [Errno 20] Not a directory: '/usr/bin/djangoapp/app/templates/index.html'

The erroneous path is clearly built from two parts: a path to exxo
binary (``/usr/bin/djangoapp``) and a path inside zip
(``app/templates/index.html``). Exxo patches several standard I/O
functions inside CPython to detect the above pattern and return an
object from zip instead of an error. This simple hack vastly improves
zip compatibility - to the point it's possible to build Django apps
out of the box.

Here's a list of functions and modules patched so far:

* ``open``

* ``os.stat``

* ``os.listdir``

* ``ctypes`` (requires unpacking to temporary location)

* ``subprocess`` (requires unpacking to temporary location)

Building exxo from sources
--------------------------

Building was tested only on Ubuntu. Python 3 is also required.

Install build dependencies with::

    apt-get install -y gcc make patch wget tar gzip bzip2 xz-utils blt-dev libbluetooth-dev libbz2-dev libc-dev-bin libc6-dev libdb4.8-dev libexpat1-dev libffi-dev libfontconfig1-dev libfreetype6-dev libncurses5-dev libncursesw5-dev libpthread-stubs0-dev libreadline-dev libreadline6-dev libsqlite3-dev libssl-dev libstdc++6-4.4-dev libx11-dev libxau-dev libxcb1-dev libxdmcp-dev libxext-dev libxft-dev libxrender-dev libxss-dev linux-libc-dev tcl8.5-dev tk8.5-dev x11proto-core-dev x11proto-input-dev x11proto-kb-dev x11proto-render-dev x11proto-scrnsaver-dev x11proto-xext-dev xtrans-dev zlib1g-dev liblzma-dev upx

Build PyRun binaries with::

    python3 -m exxo.bootstrap all

From this point exxo is usable as ``python3 -m exxo.exxo``. Type
``make build`` to build exxo binary under ``dist`` directory.

===============================
exxo
===============================

*EXPERIMENTAL*

Build portable, (mostly) statically linked Python binaries.

Python 3.5 required.

Bootstrap (you must install regular Python build dependencies first):

    python3 -m exxo.bootstrap

Build binary:

    python3 -m exxo.exxo sentry_launcher sentry_launcher.m:main /tmp/bar

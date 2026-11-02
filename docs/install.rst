.. _install:

================
Installing twill
================

The recommended way to install twill is to use pip_::

   pip install twill

You can also install it directly from a downloaded wheel or source
distribution file::

   pip install twill-3.4.0.tar.gz


Troubleshooting your installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first and only thing you should do before creating an issue_ on the
`GitHub project page`_ is to see if you have the twill package installed
correctly::

   python -m twill

(This should drop you into the twill shell irrespective of whether 'twill'
is on your path.)  **If this works**, twill is installed correctly and you
just need to make sure that the directory where pip installs scripts is on
your path. If you still need help, or the above command doesn't work, please
include its output when you create an issue -- thanks!

Upgrading twill
~~~~~~~~~~~~~~~

You can use pip to upgrade twill. To get the latest release, use::

   pip install -U twill

To download the latest development release (which is usually pretty
stable) use::

   pip install -U https://github.com/twill-tools/twill/archive/main.zip

.. _pip: https://docs.python.org/3/installing/index.html
.. _issue: https://github.com/twill-tools/twill/issues
.. _GitHub project page: https://github.com/twill-tools/twill

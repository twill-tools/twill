.. _examples:

==============
twill Examples
==============

Example: logging into slashdot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script logs you into slashdot (assuming you have an account!)::

    setlocal username <your username>
    setlocal password <your password>

    go http://www.slashdot.org/
    formvalue 1 unickname $username
    formvalue 1 upasswd $password
    submit

    code 200     # make sure form submission is correct!

Example: searching Google and going to the first hit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Please be aware that automated searching of Google violates their
Terms of Service. This is for example purposes only!*::

    setlocal query "twill Python"

    go https://www.google.com/

    fv 1 q $query
    submit btnI     # use the "I'm feeling lucky" button

    show



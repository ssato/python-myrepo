About
==============

Myrepo is a tool to help custom yum repositories management tasks such as:

* Initialize your custom yum repositories and generate config files (.repo,
  mock.cfg): myrepo init ...

* Build and deploy srpm and rpm files to yum repositories:
  myrepo deploy ... SRPM_PATH

It may be used as poor man's koji, I guess.

Usage
=======

1. Arrange system global or user configuration files in accordance with your
   environment and needs:

   Configuration files are searched from
   ["/etc/myreporc", "/etc/myrepo.d/\*.conf", "~/.myreporc"]

2. Configure ~/.gitconfig as needed. Myrepo uses its user information if
   found and not specified in configuration files:

   ~/.gitconfig Example::

     [user]
           name = John Doe
           email = jdoe@example.com

3. Add your myrepo user to mock group::

   sudo usermod -a -G mock <mock_user>

4. Confirm you can ssh to your server w/o password or passphrase.

5. Initialize your custom repositories w/ myrepo::

   myrepo i [options ...]

6. Now ready to go. Build and deploy SRPMs you want such like::

   myrepo -v d /path/to/foo-x.y.z-1.src.rpm

How to install
================

a. [Recommended] Make srpm, build rpm and install:

   1. python setup.py srpm
   2. mock dist/SRPMS/<built src.rpm>
   3. yum install -y /var/lib/mock/<your_build_dist>/results/<built rpm>

b. Build rpm and install:

   1. python setup.py rpm
   2. yum install -y dist/RPMS/noarch/<built rpm>

Hacking
=========

* Every module must passes PEP8 tests.
* Every time modifications made to myrepo modules (myrepo/\*\*/\*.py),
  corresponding tests should be run for them, e.g.::

    ./aux/runtest.sh myrepo/config.py
    ./aux/runtest.sh myrepo/tests/config.py

  and run application level tests::

    bash -x ./tests/driver.sh 2>&1 | tee /tmp/test.log

Meta
======

* Author: Satoru SATOH <ssato _at_ redhat.com>
* License: GPLv3+

TODO
------

* Write tests:

  * myrepo.tests.\*: Almost done
  * myrepo.commands.tests.\*: Almost done

.. vim:sw=2:ts=2:et:

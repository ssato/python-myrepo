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


Here is an example session log of yum repo initialization w/ using myrepo's "init" sub command::

  ssato@localhost% git config user.name
  Satoru SATOH
  ssato@localhost% git config user.email
  satoru.satoh@gmail.com
  ssato@localhost% whoami
  ssato
  ssato@localhost% grep -e '^mock' /etc/group
  mock:x:998:ssato
  ssato@localhost% rm -rf ~/public_html
  ssato@localhost% myrepo init -v --config /dev/null --dists fedora-19-x86_64 \
  > --hostname localhost --altname=yumrepos.example.com \
  > --topdir=~/public_html/yum --baseurl=http://yumrepos.example.com/~ssato/yum
  12:20:48 [INFO] myrepo: Loading config: /dev/null
  12:20:48 [DEBUG] myrepo: Use default profile
  12:20:48 [DEBUG] myrepo: repo base dist: name=fedora, ver=19, archs=['x86_64']
  12:20:48 [INFO] myrepo: Run myrepo.commands.init.run...
  12:20:48 [DEBUG] myrepo: Run: cmd=mkdir -p ~/public_html/yum/fedora/19/{x86_64,sources}, cwd=.
  12:20:48 [INFO] myrepo: Create a temporary workdir: /tmp/myrepo-workdir-mLKNrF
  12:20:48 [DEBUG] myrepo: Rewrote cmd to: cd /home/ssato/public_html/yum/fedora/19/sources && test -d repodata && createrepo --update --deltas --oldpackagedirs . --database . || createrepo --deltas --oldpackagedirs . --database .
  12:20:48 [DEBUG] myrepo: Rewrote cmd to: cd /home/ssato/public_html/yum/fedora/19/x86_64 && test -d repodata && createrepo --update --deltas --oldpackagedirs . --database . || createrepo --deltas --oldpackagedirs . --database .
  12:20:48 [INFO] myrepo: Run myrepo.commands.genconf.run...
  12:20:48 [DEBUG] myrepo: Run: cmd=mkdir -p /tmp/myrepo-workdir-mLKNrF && (cat << "EOF_a22b0d7c-2b11-11e3-a52a-081196958ea0" > /tmp/myr, cwd=.
  12:20:48 [DEBUG] myrepo: cmd=mkdir -p /tmp/myrepo-workdir-mLKNrF && (cat << "EOF_a22b0d7c-2b11-11e3-a52a-081196958ea0" > /tmp/myr, logfile=/tmp/myrepo-workdir-mLKNrF/26350.log
  ssato@localhost% ls ~/public_html/yum/fedora/19/*
  /home/ssato/public_html/yum/fedora/19/sources:
  drpms  fedora-yumrepos-ssato-release-19-1.fc19.src.rpm  repodata

  /home/ssato/public_html/yum/fedora/19/x86_64:
  drpms  fedora-yumrepos-ssato-19-mockbuild-data-19-1.fc19.noarch.rpm  fedora-yumrepos-ssato-release-19-1.fc19.noarch.rpm  repodata
  ssato@localhost% rpm -qlp \
  > ~/public_html/yum/fedora/19/x86_64/fedora-yumrepos-ssato-release-19-1.fc19.noarch.rpm
  /etc/yum.repos.d/fedora-yumrepos-ssato.repo
  ssato@localhost% ls /tmp/myrepo-workdir-mLKNrF
  26350.log  fedora-yumrepos-ssato-19-x86_64.cfg  fedora-yumrepos-ssato-19.spec
  fedora-yumrepos-ssato-release-19-1.myrepo.src.rpm  fedora-yumrepos-ssato.repo
  ssato@localhost% cat /tmp/myrepo-workdir-mLKNrF/fedora-yumrepos-ssato.repo
  [fedora-yumrepos-ssato]
  name=Custom yum repository on yumrepos.example.com by ssato
  baseurl=http://yumrepos.example.com/~ssato/yum/fedora/$releasever/$basearch/
  enabled=1
  gpgcheck=0


  [fedora-yumrepos-ssato-source]
  name=Custom yum repository on yumrepos.example.com by ssato (source)
  baseurl=http://yumrepos.example.com/~ssato/yum/fedora/$releasever/sources/
  enabled=0
  gpgcheck=0

  ssato@localhost%


And here is an example session log to build srpm and deploy RPMs w/ using myrepo's "deploy" (abbrev: 'd') sub command::

  ssato@localhost% myrepo d -v --config /dev/null --dists fedora-19-x86_64 \
  > --hostname localhost --topdir=~/public_html/yum \
  > myrepo/commands/tests/rpm-sample-1.0-1.fc19.src.rpm
  12:25:47 [INFO] myrepo: Loading config: /dev/null
  12:25:47 [DEBUG] myrepo: Use default profile
  12:25:47 [DEBUG] myrepo: repo base dist: name=fedora, ver=19, archs=['x86_64']
  12:25:47 [DEBUG] myrepo: Rewrote cmd to: cd /home/ssato/public_html/yum/fedora/19/sources && test -d repodata && createrepo --update --deltas --oldpackagedirs . --database . || createrepo --deltas --oldpackagedirs . --database .
  12:25:47 [DEBUG] myrepo: Rewrote cmd to: cd /home/ssato/public_html/yum/fedora/19/x86_64 && test -d repodata && createrepo --update --deltas --oldpackagedirs . --database . || createrepo --deltas --oldpackagedirs . --database .
  12:25:47 [INFO] myrepo: Run myrepo.commands.deploy.run...
  12:25:47 [DEBUG] myrepo: Run: cmd=mock -r fedora-19-x86_64 myrepo/commands/tests/rpm-sample-1.0-1.fc19.src.rpm && cp -a /var/lib/mock/, cwd=.
  INFO: mock.py version 1.1.33 starting...
  Start: init plugins
  INFO: tmpfs initialized
  INFO: selinux enabled
  Finish: init plugins
  Start: run
  INFO: Start(myrepo/commands/tests/rpm-sample-1.0-1.fc19.src.rpm)  Config(fedora-19-x86_64)
  Start: lock buildroot
  Start: clean chroot
  INFO: chroot (/var/lib/mock/fedora-19-x86_64) unlocked and deleted
  Finish: clean chroot
  Finish: lock buildroot
  Start: chroot init
  Start: lock buildroot
  Mock Version: 1.1.33
  INFO: Mock Version: 1.1.33
  INFO: calling preinit hooks
  INFO: mounting tmpfs at /var/lib/mock/fedora-19-x86_64/root/.
  INFO: enabled root cache
  Start: unpacking root cache
  Finish: unpacking root cache
  INFO: enabled yum cache
  Start: cleaning yum metadata
  Finish: cleaning yum metadata
  INFO: enabled ccache
  Start: device setup
  Finish: device setup
  Start: yum update
  Start: Outputting list of available packages
  Finish: Outputting list of available packages
  Finish: yum update
  Finish: lock buildroot
  Finish: chroot init
  INFO: Installed packages:
  Start: build phase for rpm-sample-1.0-1.fc19.src.rpm
  Start: device setup
  Finish: device setup
  Start: build setup for rpm-sample-1.0-1.fc19.src.rpm
  Finish: build setup for rpm-sample-1.0-1.fc19.src.rpm
  Start: rpmbuild -bb rpm-sample-1.0-1.fc19.src.rpm
  Start: Outputting list of installed packages
  Finish: Outputting list of installed packages
  Finish: rpmbuild -bb rpm-sample-1.0-1.fc19.src.rpm
  INFO: unmounting tmpfs.
  Finish: build phase for rpm-sample-1.0-1.fc19.src.rpm
  INFO: Done(myrepo/commands/tests/rpm-sample-1.0-1.fc19.src.rpm) Config(fedora-19-x86_64) 0 minutes 17 seconds
  INFO: Results and/or logs in: /var/lib/mock/fedora-19-x86_64/result
  Finish: run
  Spawning worker 0 with 1 pkgs
  Spawning worker 1 with 0 pkgs
  Spawning worker 2 with 0 pkgs
  Spawning worker 3 with 0 pkgs
  Workers Finished
  Saving Primary metadata
  Saving file lists metadata
  Saving other metadata
  Saving delta metadata
  Generating sqlite DBs
  Sqlite DBs complete
  Spawning worker 0 with 1 pkgs
  Spawning worker 1 with 0 pkgs
  Spawning worker 2 with 0 pkgs
  Spawning worker 3 with 0 pkgs
  Workers Finished
  Saving Primary metadata
  Saving file lists metadata
  Saving other metadata
  Saving delta metadata
  Generating sqlite DBs
  Sqlite DBs complete
  ssato@localhost% ls ~/public_html/yum/fedora/19/*
  /home/ssato/public_html/yum/fedora/19/sources:
  drpms  fedora-yumrepos-ssato-release-19-1.fc19.src.rpm  repodata  rpm-sample-1.0-1.fc19.src.rpm

  /home/ssato/public_html/yum/fedora/19/x86_64:
  drpms  fedora-yumrepos-ssato-19-mockbuild-data-19-1.fc19.noarch.rpm
  fedora-yumrepos-ssato-release-19-1.fc19.noarch.rpm  repodata
  rpm-sample-1.0-1.fc19.noarch.rpm
  ssato@localhost%

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

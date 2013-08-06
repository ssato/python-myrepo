python-myrepo
=============

A tool to manage custom yum repositories: Initialize your custom yum
repositories, update meta data of yum repositories, build and deploy source
rpms to yum repositories, etc


How to install
================

a. [Recommended] Make srpm, build rpm and install:

   1. python setup.py srpm
   2. mock dist/SRPMS/<built src.rpm>
   3. yum install -y /var/lib/mock/<your_build_dist>/results/<built rpm>

b. Build rpm and install:

   1. python setup.py rpm
   3. yum install -y dist/RPMS/noarch/<built rpm>


How to use
================

1. Arrange system global or user configuration files in accordance with your
   environment and needs:

   Configuration files are searched from
   ["/etc/myreporc", "/etc/myrepo.d/*.conf", "~/.myreporc"]

2. Configure ~/.gitconfig as needed. Myrepo uses its user information if
   found and not specified in configuration files:

   ~/.gitconfig Example:

   [user]
           name = John Doe
           email = jdoe@example.com

3. Add your myrepo user to mock group:

   sudo usermod -a -G mock <mock_user>


4. Initialize your custom repositories w/ myrepo:

   myrepo i [options ...]

5. Now ready to go. Build and deploy SRPMs you want such like:

   myrepo -v d /path/to/foo-x.y.z-1.src.rpm



Meta
=============

Author: Satoru SATOH <ssato _at_ redhat.com>
License: GPLv3+

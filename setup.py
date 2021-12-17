#!/usr/bin/env python
# Copyright (C) 2016-2019 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - https://cuckoosandbox.org/.
#  See the file 'docs/LICENSE' for copying permission.

import hashlib
import os
import setuptools
import sys
import traceback

if sys.version[0] == "3":
    sys.exit(
        "Cuckoo is Python2-only at the moment! Please use Python 2 to "
        "install it, i.e., `pip2 install -U cuckoo`."
    )

# Update the MANIFEST.in file to include the one monitor version that is
# actively shipped for this distribution and exclude all the other monitors
# that we have lying around. Note: I tried to do this is in a better manner
# through exclude_package_data, but without much luck.

excl, monitor = [], os.path.join("cuckoo", "data", "monitor")
latest = open(os.path.join(monitor, "latest"), "rb").read().strip()
for h in os.listdir(monitor):
    if h != "latest" and h != latest:
        excl.append(
            "recursive-exclude cuckoo/data/monitor/%s *  # AUTOGENERATED" % h
        )

if not os.path.isdir(os.path.join(monitor, latest)):
    sys.exit(
        "Failure locating the monitoring binaries that belong to the latest "
        "monitor release. Please include those to create a distribution. "
        "You may easily obtain the monitoring binaries by running one of our "
        "helper scripts: 'python stuff/monitor.py'."
    )

manifest = []
for line in open("MANIFEST.in", "rb"):
    if not line.strip() or "# AUTOGENERATED" in line:
        continue

    manifest.append(line.strip())

manifest.extend(excl)

open("MANIFEST.in", "wb").write("\n".join(manifest) + "\n")

def githash():
    """Extracts the current Git hash."""
    git_value = os.path.join(".git", "HEAD")
    while True:
        if os.path.exists(git_value):
            git_value = open(git_value, "rb").read().strip()
            continue

        if git_value.startswith("ref: "):
            git_value = os.path.join(".git", git_value.split()[1])
            continue

        return git_value

cwd_public = os.path.join("cuckoo", "data")
cwd_private = os.path.join("cuckoo", "private")

hashes_ignore = (
    "safelist/domain.txt",
)

def update_hashes():
    hashes, hashes_r = {}, {}
    for line in open(os.path.join(cwd_private, "cwd", "hashes.txt"), "rb"):
        if not line.strip() or line.startswith("#"):
            continue
        hash_, filename = line.split()
        hashes[filename] = hashes.get(filename, []) + [hash_]
        hashes_r[filename] = True

    new_hashes = []
    for dirpath, dirnames, filenames in os.walk(cwd_public):
        dirname = dirpath[len(cwd_public)+1:]
        for filename in filenames:
            if filename.endswith((".pyc", ".DS_Store")):
                continue
            filepath = os.path.join(dirname, filename).replace("\\", "/")
            if filepath in hashes_ignore:
                continue
            buf = open(os.path.join(cwd_public, filepath), "rb").read()
            hash_ = hashlib.sha1(buf).hexdigest()
            if filepath not in hashes or hash_ not in hashes[filepath]:
                new_hashes.append((filepath, hash_))
            hashes_r.pop(filepath, None)

    for filepath in hashes_r:
        if hashes[filepath][-1] != "0"*40:
            new_hashes.append((filepath, "0"*40))

    with open(os.path.join(cwd_private, "cwd", "hashes.txt"), "a+b") as f:
        new_hashes and f.write("\n")
        for filename, hash_ in sorted(new_hashes):
            f.write("%s %s\n" % (hash_, filename))

# Provide hashes for our CWD migration process & update the $CWD/.cwd version.
# Only do these steps when "python setup.py sdist" is invoked.
if "setup.py" in sys.argv and "sdist" in sys.argv:
    update_hashes()
    cwd_filepath = os.path.join(cwd_private, ".cwd")
    open(cwd_filepath, "wb").write(githash())

def do_help(e, message):
    if isinstance(e, ValueError) and "jpeg is required" in e.message:
        print("  This particular error may be resolved as follows:")
        print("      sudo apt-get install libjpeg-dev")

    if isinstance(e, ValueError) and "zlib is required" in e.message:
        print("  This particular error may be resolved as follows:")
        print("      sudo apt-get install zlib1g-dev")

    if isinstance(e, SystemExit) and "x86_64-linux-gnu-gcc" in e.message:
        print("  This particular error *may* be resolved as follows:")
        print("      sudo apt-get install python-dev libffi-dev libssl-dev")

    print("  But don't forget to check out our documentation for full")
    print("  installation steps. You might also want to check our FAQ.")

def do_setup(**kwargs):
    try:
        setuptools.setup(**kwargs)
    except (SystemExit, Exception) as e:
        print("\x1b[31m")
        print("The following error has occurred while trying to install Cuckoo!")
        print("\x1b[0m")
        print(traceback.format_exc())
        print("\x1b[31m")
        print("Make sure that you've installed all requirements for Cuckoo ")
        print("to be installed properly! Please refer to our documentation: ")
        print("https://cuckoo.sh/docs/installation/host/requirements.html")
        print("\x1b[33m")
        print("Once you have triple checked that all dependencies have been ")
        print("installed but Cuckoo still fails, please feel free to reach ")
        print("out to us on IRC / email / Github!")
        print("\x1b[0m")

        if hasattr(e, "message") and isinstance(e.message, basestring):
            do_help(e, e.message)

        exit(1)

do_setup(
    name="Cuckoo",
    version="2.0.7",
    author="Stichting Cuckoo Foundation",
    author_email="cuckoo@cuckoofoundation.org",
    packages=[
        "cuckoo",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Flask",
        "Framework :: Pytest",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Topic :: Security",
    ],
    keywords=(
        "cuckoo sandbox automated malware analysis project threat "
        "intelligence cert soc"
    ),
    url="https://cuckoosandbox.org/",
    license="GPLv3",
    description="Automated Malware Analysis System",
    long_description=open("README.rst", "rb").read(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "cuckoo = cuckoo.main:main",
        ],
    },
    install_requires=[
        "alembic==1.0.10",
        "androguard==3.0.1",
        "beautifulsoup4==4.5.3",
        "chardet==2.3.0",
        "click==6.6",
        "django==1.8.4",
        "django_extensions==1.6.7",
        "dpkt==1.8.7",
        "egghatch>=0.2.3, <0.3",
        "elasticsearch==5.3.0",
        "flask==0.12.2",
        "flask-sqlalchemy==2.4.0",
        "httpreplay>=0.2.4, <0.3",
        "ipaddress>=1.0.22",
        "gevent>=1.2, <1.3",
        "jinja2==2.9.6",
        "jsbeautifier==1.6.2",
        "oletools==0.51",
        "peepdf>=0.4.2, <0.5",
        "pefile2==1.2.11",
        "pillow==3.2",
        "pyelftools==0.24",
        "pyguacamole==0.6",
        "pymisp==2.4.106",
        "pymongo==3.0.3",
        "python-dateutil==2.4.2",
        "python-magic==0.4.12",
        "roach>=0.1.2, <0.2",
        "sflock>=0.3.10, <0.4",
        "sqlalchemy==1.3.3",
        "unicorn==1.0.1",
        "wakeonlan==0.2.2",
        "yara-python==3.6.3",
    ],
    extras_require={
        ":sys_platform == 'win32'": [
            "requests==2.13.0",
        ],
        ":sys_platform == 'darwin'": [
            "requests==2.13.0",
        ],
        ":sys_platform == 'linux2'": [
            "requests[security]==2.13.0",
            "scapy==2.3.2",
        ],
        "distributed": [
            "psycopg2==2.6.2",
        ],
        "postgresql": [
            "psycopg2==2.6.2",
        ],
        "weasyprint": [
            "weasyprint==0.36",
        ],
    },
)

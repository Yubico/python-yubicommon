# Copyright (c) 2013 Yubico AB
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that the following
#   conditions are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

__version__ = '0.1.0'
__dependencies__ = []
__all__ = ['get_version', 'setup', 'release']


from setuptools import setup as _setup, find_packages, Command
from distutils import log
from distutils.errors import DistutilsSetupError
from datetime import date
import os
import re

VERSION_PATTERN = re.compile(r"(?m)^__version__\s*=\s*['\"](.+)['\"]$")
DEPENDENCY_PATTERN = re.compile(
    r"(?m)__dependencies__\s*=\s*\[((['\"].+['\"]\s*(,\s*)?)+)\]")


def get_version(module_name=None):
    """Return the current version as defined by the given module."""

    if module_name is None:
        parts = __name__.split('.')
        module_name = parts[0] if len(parts) > 1 else find_packages()[0]

    with open('%s/__init__.py' % module_name, 'r') as f:
        match = VERSION_PATTERN.search(f.read())
        return match.group(1)


def get_dependencies(module):
    basedir = os.path.dirname(__file__)
    fn = os.path.join(basedir, module, '__init__.py')
    if os.path.isfile(fn):
        with open(fn, 'r') as f:
            match = DEPENDENCY_PATTERN.search(f.read())
            if match:
                return map(lambda s: s.strip().strip('"\''),
                           match.group(1).split(','))
    return []


def get_package(module):
    return __name__ + '.' + module


def setup(**kwargs):
    if 'version' not in kwargs:
        kwargs['version'] = get_version()
    packages = kwargs.setdefault('packages',
                                 find_packages(exclude=[__name__ + '.*']))
    install_requires = kwargs.setdefault('install_requires', [])
    for yc_module in kwargs.pop('yc_requires', []):
        packages.append(get_package(yc_module))
        for dep in get_dependencies(yc_module):
            if dep not in install_requires:
                install_requires.append(dep)
    cmdclass = kwargs.setdefault('cmdclass', {})
    cmdclass.setdefault('release', release)
    return _setup(**kwargs)


class release(Command):
    description = "create and release a new version"
    user_options = [
        ('keyid', None, "GPG key to sign with"),
        ('skip-tests', None, "skip running the tests"),
        ('pypi', None, "publish to pypi"),
    ]
    boolean_options = ['skip-tests', 'pypi']

    def initialize_options(self):
        self.keyid = None
        self.skip_tests = 0
        self.pypi = 0

    def finalize_options(self):
        self.cwd = os.getcwd()
        self.fullname = self.distribution.get_fullname()
        self.name = self.distribution.get_name()
        self.version = self.distribution.get_version()

    def _verify_version(self):
        with open('NEWS', 'r') as news_file:
            line = news_file.readline()
        now = date.today().strftime('%Y-%m-%d')
        if not re.search(r'Version %s \(released %s\)' % (self.version, now),
                         line):
            raise DistutilsSetupError("Incorrect date/version in NEWS!")

    def _verify_tag(self):
        if os.system('git tag | grep -q "^%s\$"' % self.fullname) == 0:
            raise DistutilsSetupError(
                "Tag '%s' already exists!" % self.fullname)

    def _sign(self):
        if os.path.isfile('dist/%s.tar.gz.asc' % self.fullname):
            # Signature exists from upload, re-use it:
            sign_opts = ['--output dist/%s.tar.gz.sig' % self.fullname,
                         '--dearmor dist/%s.tar.gz.asc' % self.fullname]
        else:
            # No signature, create it:
            sign_opts = ['--detach-sign', 'dist/%s.tar.gz' % self.fullname]
            if self.keyid:
                sign_opts.insert(1, '--default-key ' + self.keyid)
        self.execute(os.system, ('gpg ' + (' '.join(sign_opts)),))

        if os.system('gpg --verify dist/%s.tar.gz.sig' % self.fullname) != 0:
            raise DistutilsSetupError("Error verifying signature!")

    def _tag(self):
        tag_opts = ['-s', '-m ' + self.fullname, self.fullname]
        if self.keyid:
            tag_opts[0] = '-u ' + self.keyid
        self.execute(os.system, ('git tag ' + (' '.join(tag_opts)),))

    def run(self):
        if os.getcwd() != self.cwd:
            raise DistutilsSetupError("Must be in package root!")

        self._verify_version()
        self._verify_tag()
        self.run_command('check')

        self.execute(os.system, ('git2cl > ChangeLog',))

        self.run_command('sdist')

        if not self.skip_tests:
            try:
                self.run_command('test')
            except SystemExit as e:
                if e.code != 0:
                    raise DistutilsSetupError("There were test failures!")

        if self.pypi:
            cmd_obj = self.distribution.get_command_obj('upload')
            cmd_obj.sign = True
            if self.keyid:
                cmd_obj.identity = self.keyid
            self.run_command('upload')

        self._sign()
        self._tag()

        self.announce("Release complete! Don't forget to:", log.INFO)
        self.announce("")
        self.announce("    git push && git push --tags", log.INFO)
        self.announce("")

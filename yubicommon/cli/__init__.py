# Copyright (c) 2016 Yubico AB
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

from __future__ import absolute_import
from __future__ import print_function

from docopt import docopt, DocoptExit
import sys

from .. import compat

__all__ = ['CliCommand', 'Argument']


# From PEP 0257 -- Docstring Conventions (Public Domain)
def trim(docstring):
    """Corrects indentation for docstrings"""
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


class Argument(object):
    """
    Single argument in a subclass of CliCommand.

    key should be the name of the parameter in the docopt string,
    or an iterable containing mutually exclusive commands.

    See CliCommand for example usage.
    """

    def __init__(self, key, santitize=lambda x: x, default=None):
        self._key = key
        self._sanitize = santitize
        self._default = default

    def __get__(self, instance, objtype):
        return getattr(self, '_value', self)

    def set_value(self, args):
        if isinstance(self._key, compat.string_types):
            value = args[self._key]
        else:
            value = None
            for key in self._key:
                if args.get(key, False) is True:
                    value = key
                    break
        self._value = self._sanitize(value) \
            if value is not None else self._default


class CliCommand(object):
    """
    A command in a CLI program, using a docopt compatitbe docstring.

    Use the Argument class to help parse the arguments, which are provided by
    docopt, either passed to the constructor or read from sys.argv.

    For example:

    class Foo(CliCommand):
        \"\"\"
        Usage:
            foo add [--count N]
            foo rm
        \"\"\"

        subcommand = Argument(['add', 'rm'])  # Will be 'add' or 'rm'
        count = Argument('--count', int, 5)  # Will be an int, defaulting to 5

        def do_something(self):
            if self.subcommand == 'add':
                self.add(self.count)
            elif self.subcommand == 'rm':
                self.remove()
    """

    def __init__(self, *args, **kwargs):
        # Parse args
        self._args = docopt(trim(self.__doc__), *args, **kwargs)

        # Populate Arguments from args
        for f in dir(self):
            arg = getattr(self, f)
            if isinstance(arg, Argument):
                try:
                    arg.set_value(self._args)
                except (ValueError, TypeError) as e:
                    print("Error for option {}: {}".format(arg._key, e))
                    raise DocoptExit()

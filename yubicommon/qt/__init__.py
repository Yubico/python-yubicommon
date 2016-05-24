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

from __future__ import absolute_import

from PySide import QtGui
from .utils import *
from .classes import *
from .worker import *
from .settings import *
import sys
import traceback


# Font fixes for OSX
if sys.platform == 'darwin':
    from platform import mac_ver
    mac_version = tuple(int(x) for x in mac_ver()[0].split('.'))
    if (10, 9) <= mac_version < (10, 10):  # Mavericks
        QtGui.QFont.insertSubstitution('.Lucida Grande UI', 'Lucida Grande')
    if (10, 10) <= mac_version:  # Yosemite
        QtGui.QFont.insertSubstitution('.Helvetica Neue DeskInterface',
                                       'Helvetica Neue')


# Replace excepthook with one that releases the exception to prevent memory
# leaks:
def excepthook(typ, val, tback):
    try:
        traceback.print_exception(typ, val, tback)
        sys.exc_clear()
        del sys.last_value
        del sys.last_traceback
        del sys.last_type
    except:
        pass  # Ignore failure here, we're likely shutting down...
sys.excepthook = excepthook

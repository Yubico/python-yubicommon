# Copyright (c) 2014 Yubico AB
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Additional permission under GNU GPL version 3 section 7
#
# If you modify this program, or any covered work, by linking or
# combining it with the OpenSSL project's OpenSSL library (or a
# modified version of that library), containing parts covered by the
# terms of the OpenSSL or SSLeay licenses, We grant you additional
# permission to convey the resulting work. Corresponding Source for a
# non-source form of such a combination shall include the source code
# for the parts of OpenSSL used as well as that of the covered work.

from __future__ import absolute_import

from PySide import QtCore, QtGui
from functools import wraps
from inspect import getargspec

__all__ = ['get_text', 'get_active_window', 'is_minimized', 'connect_once']


class _DefaultMessages(object):

    def __init__(self, default_m, m=None):
        self._defaults = default_m
        self._m = m

    def __getattr__(self, method_name):
        if hasattr(self._m, method_name):
            return getattr(self._m, method_name)
        else:
            return getattr(self._defaults, method_name)

def default_messages(_m, name='m'):
    def inner(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            index = getargspec(fn).args.index(name)
            if len(args) > index:
                args = list(args)
                args[index] = _DefaultMessages(_m, args[index])
            else:
                kwargs[name] = _DefaultMessages(_m, kwargs.get(name))
            return fn(*args, **kwargs)
        return wrapper
    return inner


def get_text(*args, **kwargs):
    flags = (
        QtCore.Qt.WindowTitleHint |
        QtCore.Qt.WindowSystemMenuHint
    )
    kwargs['flags'] = flags
    return QtGui.QInputDialog.getText(*args, **kwargs)


def get_active_window():
    active_win = QtGui.QApplication.activeWindow()
    if active_win is not None:
        return active_win

    wins = [w for w in QtGui.QApplication.topLevelWidgets()
            if isinstance(w, QtGui.QDialog) and w.isVisible()]

    if not wins:
        return QtCore.QCoreApplication.instance().window

    return wins[0]  # TODO: If more than one candidates remain, find best one.


def connect_once(signal, slot):
    def wrapped(*args, **kwargs):
        signal.disconnect(wrapped)
        slot(*args, **kwargs)
    signal.connect(wrapped)


def is_minimized(window):
    """Returns True iff the window is minimized or has been sent to the tray"""
    return not window.isVisible() or window.isMinimized()

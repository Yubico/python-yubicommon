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

from PySide import QtGui, QtCore
from functools import partial
from os import getenv
from .utils import connect_once, get_active_window, default_messages
import traceback


class _Messages(object):
    wait = 'Please wait...'


class _Event(QtCore.QEvent):
    EVENT_TYPE = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

    def __init__(self, callback):
        super(_Event, self).__init__(_Event.EVENT_TYPE)
        self._callback = callback

    def callback(self):
        self._callback()
        del self._callback


class Worker(QtCore.QObject):
    _work_signal = QtCore.Signal(tuple)
    _work_done_0 = QtCore.Signal()

    @default_messages(_Messages)
    def __init__(self, window, m):
        super(Worker, self).__init__()
        self.m = m
        self.window = window
        self._work_signal.connect(self.work)
        self.work_thread = QtCore.QThread()
        self.moveToThread(self.work_thread)
        self.work_thread.start()

    def post(self, title, fn, callback=None, return_errors=False):
        busy = QtGui.QProgressDialog(title, None, 0, 0, get_active_window())
        busy.setWindowTitle(self.m.wait)
        busy.setWindowModality(QtCore.Qt.WindowModal)
        busy.setMinimumDuration(0)
        busy.setWindowFlags(
            busy.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        busy.show()
        connect_once(self._work_done_0, busy.close)
        self.post_bg(fn, callback, return_errors)

    def post_bg(self, fn, callback=None, return_errors=False):
        if isinstance(fn, tuple):
            fn = partial(fn[0], *fn[1:])
        self._work_signal.emit((fn, callback, return_errors))

    def post_fg(self, fn):
        if isinstance(fn, tuple):
            fn = partial(fn[0], *fn[1:])
        event = _Event(fn)
        QtGui.QApplication.postEvent(self.window, event)

    @QtCore.Slot(tuple)
    def work(self, job):
        QtCore.QThread.msleep(10)  # Needed to yield
        (fn, callback, return_errors) = job
        try:
            result = fn()
        except Exception as e:
            result = e
            if getenv('DEBUG'):
                traceback.print_exc()
            if not return_errors:
                def callback(e): raise e
        if callback:
            event = _Event(partial(callback, result))
            QtGui.QApplication.postEvent(self.window, event)
        self._work_done_0.emit()

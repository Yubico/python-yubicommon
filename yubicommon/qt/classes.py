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
from .worker import Worker
import os
import sys
import importlib
from .. import compat

__all__ = ['Application', 'Dialog', 'MutexLocker']

TOP_SECTION = '<b>%s</b>'
SECTION = '<br><b>%s</b>'


class Dialog(QtGui.QDialog):

    def __init__(self, *args, **kwargs):
        super(Dialog, self).__init__(*args, **kwargs)
        self.setWindowFlags(self.windowFlags() ^
                            QtCore.Qt.WindowContextHelpButtonHint)
        self._headers = _Headers()

    @property
    def headers(self):
        return self._headers

    def section(self, title):
        return self._headers.section(title)


class _Headers(object):

    def __init__(self):
        self._first = True

    def section(self, title):
        if self._first:
            self._first = False
            section = TOP_SECTION % title
        else:
            section = SECTION % title
        return QtGui.QLabel(section)


class _MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(_MainWindow, self).__init__()
        self._widget = None

    def hide(self):
        if sys.platform == 'darwin':
            from .osx import app_services
            app_services.osx_hide()
        else:
            super(_MainWindow, self).hide()

    def customEvent(self, event):
        event.callback()
        event.accept()


class Application(QtGui.QApplication):
    _quit = False

    def __init__(self, m=None, version=None):
        super(Application, self).__init__(sys.argv)
        self._determine_basedir()
        self._read_package_version(version)

        self.window = _MainWindow()

        if m:  # Run all strings through Qt translation
            for key in dir(m):
                if (isinstance(key, compat.string_types) and
                        not key.startswith('_')):
                    setattr(m, key, self.tr(getattr(m, key)))

        self.worker = Worker(self.window, m)

    def _determine_basedir(self):
        if getattr(sys, 'frozen', False):
            # we are running in a PyInstaller bundle
            self.basedir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            top_module_str = __package__.split('.')[0]
            top_module = importlib.import_module(top_module_str)
            self.basedir = os.path.dirname(top_module.__file__)

    def _read_package_version(self, version):
        if version is None:
            return

        pversion_fn = os.path.join(self.basedir, 'package_version.txt')
        try:
            with open(pversion_fn, 'r') as f:
                pversion = int(f.read().strip())
        except:
            pversion = 0

        if pversion > 0:
            version += '.%d' % pversion

        self.version = version

    def ensure_singleton(self, name=None):
        if not name:
            name = self.applicationName()
        from PySide import QtNetwork
        self._l_socket = QtNetwork.QLocalSocket()
        self._l_socket.connectToServer(name, QtCore.QIODevice.WriteOnly)
        if self._l_socket.waitForConnected():
            self._stop()
            sys.exit(0)
        else:
            self._l_server = QtNetwork.QLocalServer()
            if not self._l_server.listen(name):
                QtNetwork.QLocalServer.removeServer(name)
                self._l_server.listen(name)
            self._l_server.newConnection.connect(self._show_window)

    def _show_window(self):
        self.window.show()
        self.window.activateWindow()

    def quit(self):
        super(Application, self).quit()
        self._quit = True

    def _stop(self):
        worker_thread = self.worker.thread()
        worker_thread.quit()
        worker_thread.wait()
        self.deleteLater()
        sys.stdout.flush()
        sys.stderr.flush()

    def exec_(self):
        if not self._quit:
            status = super(Application, self).exec_()
        else:
            status = 0
        self._stop()
        return status


class MutexLocker(object):

    """Drop-in replacement for QMutexLocker that can start unlocked."""

    def __init__(self, mutex, lock=True):
        self._mutex = mutex
        self._locked = False
        if lock:
            self.relock()

    def lock(self, try_lock=False):
        if try_lock:
            self._locked = self._mutex.tryLock()
        else:
            self._mutex.lock()
            self._locked = True
        return self._locked and self or None

    def relock(self):
        self.lock()

    def unlock(self):
        if self._locked:
            self._mutex.unlock()

    def __del__(self):
        self.unlock()

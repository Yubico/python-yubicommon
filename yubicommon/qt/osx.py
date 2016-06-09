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

import ctypes
from ..ctypes import CLibrary

__all__ = ['app_services']


class ProcessSerialNumber(ctypes.Structure):
    _fields_ = [('highLongOfPsn', ctypes.c_uint32),
                ('lowLongOfPSN', ctypes.c_uint32)]


class ApplicationServices(CLibrary):
    ShowHideProcess = [ctypes.POINTER(ProcessSerialNumber), ctypes.c_bool], None
    GetFrontProcess = [ctypes.POINTER(ProcessSerialNumber)], None

    def osx_hide(self):
        """ Hide the window and let the dock
        icon be able to show the window again. """
        psn = ProcessSerialNumber()
        self.GetFrontProcess(ctypes.byref(psn))
        self.ShowHideProcess(ctypes.byref(psn), False)

app_services = ApplicationServices('ApplicationServices')

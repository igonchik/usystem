#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
pip install pyqt5
pip install pyopenssl
pip install paramiko
pip install psutil
pip install configparser
pip install aiohttp
pip install cchardet
pip install aiodns
pip install pyopenssl
"""

# pyinstall --onefile --noconsole --icon=app.ico main_client.py

import sys
import os
from PyQt5 import QtGui, QtCore, QtWidgets
from locale import getdefaultlocale
try:
    from client.transport import UTransport
except:
    from transport import UTransport
from multiprocessing import Pool
import _thread
import platform
import webbrowser


ADMIN_PIN = ''


class WindowsInhibitor:
    '''Prevent OS sleep/hibernate in windows; code from:
    https://github.com/h3llrais3r/Deluge-PreventSuspendPlus/blob/master/preventsuspendplus/core.py
    API documentation:
    https://msdn.microsoft.com/en-us/library/windows/desktop/aa373208(v=vs.85).aspx'''
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __init__(self):
        pass

    def inhibit(self):
        import ctypes
        print("Preventing Windows from going to sleep")
        ctypes.windll.kernel32.SetThreadExecutionState(
            WindowsInhibitor.ES_CONTINUOUS | \
            WindowsInhibitor.ES_SYSTEM_REQUIRED)

    def uninhibit(self):
        import ctypes
        print("Allowing Windows to go to sleep")
        ctypes.windll.kernel32.SetThreadExecutionState(
            WindowsInhibitor.ES_CONTINUOUS)


class LogInGroup(QtWidgets.QDialog):
    def closeEvent(self, evnt):
        evnt.ignore()
        self.hide()

    def enterPin(self):
        pin = ''
        for i in range(6):
            if len(self.pin_box[i].text()) == 0:
                return
            else:
                pin = '{0}{1}'.format(pin, self.pin_box[i].text())
        global ADMIN_PIN
        ADMIN_PIN = pin
        self.hide()

    def onTextChanged(self):
        for i in range(6):
            if len(self.pin_box[i].text()) == 0:
                self.pin_box[i].setFocus()
                return
        self.enterPin()

    def __init__(self, parent=None):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        QtWidgets.QDialog.__init__(self, None)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setFixedSize(260, 80)
        self.setWindowTitle(u'Подключение к группе')
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.current_dir, 'img', 'security-low.png')))
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint
                            & ~QtCore.Qt.WindowContextHelpButtonHint)

        layout = QtWidgets.QHBoxLayout(self)
        self.pin_box = []
        for i in range(6):
            self.pin_box.append(QtWidgets.QLineEdit(self))
            self.pin_box[i].setEchoMode(QtWidgets.QLineEdit.Password)
            font = self.pin_box[i].font()
            font.setPointSize(32)
            self.pin_box[i].setFont(font)
            self.pin_box[i].setStyleSheet("border-radius: 10px;")
            self.pin_box[i].setMaxLength(1)
            self.pin_box[i].textChanged.connect(self.onTextChanged)
            layout.addWidget(self.pin_box[i])

        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class UGuiClient:
    def send_task(self, text):
        pass

    def get_task(self):
        pass

    def close(self):
        self.usystem.usysapp.close()
        if platform.system() == 'Windows':
            import winreg
            # TODO: hibernation
            # osSleep = WindowsInhibitor()
            # osSleep.uninhibit()
            try:
                subkey = "*\\shell\\Send to USystem\\command"
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, subkey)
                subkey = "*\\shell\\Send to USystem"
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, subkey)
            except:
                pass
        sys.exit()

    def helpmedef(self, reason=0):
        #webbrowser.open('https://google.com?guid='+str(self.usystem_uid), new=2)
        webbrowser.open('http://help2.acomps.ru/?m=prime-vaio.root.ruselkom&g=root.ruselkom&a=449011636951146', new=2)

    def admin_logindef(self):
        self.usystem.adminpin = ''
        self.help_dialog = LogInGroup()
        self.help_dialog.exec_()
        global ADMIN_PIN
        self.usystem.adminpin = ADMIN_PIN
        ADMIN_PIN = '******'
        if self.usystem_gid:
            self.usystem.goout = self.usystem_gid

    def admin_logoutdef(self):
        if self.usystem_gid:
            self.usystem.goout = self.usystem_gid

    def touch_allowdef(self):
        self.security_option = 1
        self.tools.setTitle(self.statustext_high)
        self.tools.setIcon(self.statusicon_high)
        self.trayIcon.setIcon(self.statusicon_high)
        self.usystem.policy = 0

    def touch_mediumdef(self):
        self.security_option = 2
        self.trayIcon.setIcon(self.statusicon_medium)
        self.tools.setTitle(self.statustext_medium)
        self.tools.setIcon(self.statusicon_medium)
        self.usystem.policy = 1

    def touch_disdef(self):
        self.security_option = 3
        self.usystem.usysapp.close()
        self.tools.setTitle(self.statustext_low)
        self.tools.setIcon(self.statusicon_low)
        self.trayIcon.setIcon(self.statusicon_low)
        self.usystem.policy = 2

    def get_cert_info(self):
        import OpenSSL.crypto as crypto
        o = ''
        cn = ''
        try:
            st_cert = open(self.usystem.usysapp.cert, 'rt').read()
            x509 = crypto.load_certificate(crypto.FILETYPE_PEM, st_cert)
            o = x509.get_subject().O
            cn = x509.get_subject().CN
        except:
            pass
        self.usystem_uid = cn
        if o != '':
            self.usystem_gid = o
            self.trayIcon.setToolTip(u"Пользователь: {0}\nГруппа: {1}".format(self.usystem_uid, self.usystem_gid))
        else:
            self.trayIcon.setToolTip(u"Пользователь: {0}\nГруппа: Нет".format(self.usystem_uid))
            self.admin_logout.setEnabled(False)

    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.usystem = UTransport(usystem_context=self.current_dir)
        self.usystem_uid = ''
        self.usystem_gid = ''
        _thread.start_new_thread(self.usystem.thread_transport, ())

        locale = getdefaultlocale()
        translator = QtCore.QTranslator(self.app)
        translator.load(os.path.join(self.current_dir, 'locale', 'qt_%s.qm' % locale[0]))
        self.app.installTranslator(translator)
        self.trayIcon = QtWidgets.QSystemTrayIcon()
        self.trayIcon.activated.connect(self.helpmedef)
        self.statusicon_low = QtGui.QIcon(os.path.join(self.current_dir, 'img', 'security-low.png'))
        self.statusicon_high = QtGui.QIcon(os.path.join(self.current_dir, 'img', 'security-hight.png'))
        self.statusicon_medium = QtGui.QIcon(os.path.join(self.current_dir, 'img', 'security-medium.png'))
        self.statustext_low = u"Запретить соединения"
        self.statustext_medium = u"Подтверждать соединения"
        self.statustext_high = u"Принимать соединения"
        self.security_option = 1
        self.trayIcon.setIcon(self.statusicon_high)
        menu = QtWidgets.QMenu()
        self.tools = menu.addMenu(self.statusicon_high, self.statustext_high)
        menu.addSeparator()
        touch_allow = self.tools.addAction(self.statusicon_high, self.statustext_high)
        touch_medium = self.tools.addAction(self.statusicon_medium, self.statustext_medium)
        touch_dis = self.tools.addAction(self.statusicon_low, self.statustext_low)
        administration = menu.addMenu(u"Настройки")
        admin_login = administration.addAction(u"Вступить в группу")
        self.admin_logout = administration.addAction(u"Выйти из группы")
        helpme = menu.addAction(u"Удаленный помощник")
        exit_btn = menu.addAction(u"Выйти")
        menu.addAction(exit_btn)
        self.trayIcon.setContextMenu(menu)
        helpme.triggered.connect(self.helpmedef)
        admin_login.triggered.connect(self.admin_logindef)
        self.admin_logout.triggered.connect(self.admin_logoutdef)
        touch_allow.triggered.connect(self.touch_allowdef)
        touch_medium.triggered.connect(self.touch_mediumdef)
        touch_dis.triggered.connect(self.touch_disdef)
        exit_btn.triggered.connect(self.close)
        self.trayIcon.show()
        self.get_cert_info()

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    app = UGuiClient()
    osSleep = None
    hKey = None
    if platform.system() == 'Windows':
        osSleep = WindowsInhibitor()
        osSleep.inhibit()
        import winreg
        subkey = "*\\shell\\Send to USystem\\command"
        hKey = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, subkey)
        winreg.SetValueEx(hKey, None, 0, winreg.REG_SZ, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                     "filesend.exe"))

    app.run()

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

import sys
import os
from PyQt5 import QtGui, QtCore, QtWidgets
from locale import getdefaultlocale
from client.transport import UTransport
from multiprocessing import Pool
import _thread


ADMIN_PIN = ''


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


class HelpDialog(QtWidgets.QDialog):
    def closeEvent(self, evnt):
        evnt.ignore()
        self.hide()

    def enterPin(self):
        pass

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.stnl = None
        self.p12name = ''
        self.pin = ''
        self.setFixedSize(260, 130)
        self.setWindowTitle(u'Защищённое соединение')
        self.setWindowIcon(QtGui.QIcon('/usr/share/icons/fly-astra/64x64/status/dialog-password.png'))
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowMinMaxButtonsHint
                            & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.title_pin = QtWidgets.QLabel(u'Задайте пароль администратора:', self)
        self.pin_box = QtWidgets.QLineEdit(self)
        self.pin_box.setEchoMode(QtWidgets.QLineEdit.Password)
        self.send_btn = QtWidgets.QPushButton(u'Подтвердить')
        self.send_btn.clicked.connect(self.enterPin)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.title_pin)
        layout.addWidget(self.pin_box)
        layout.addWidget(self.send_btn)

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
        sys.exit()

    def helpmedef(self):
        pool = Pool(processes=1)
        pool.apply_async(self.usystem.usysapp.run_tun, [5930])
        if self.usystem_gid:
            self.help_dialog = HelpDialog()
            self.help_dialog.show()
        else:
            QtWidgets.QMessageBox.about(self, u"Ошибка!", u"Не удалось завершить соединение!")

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
        self.usystem = UTransport()
        self.usystem_uid = ''
        self.usystem_gid = ''
        _thread.start_new_thread(self.usystem.thread_transport, ())

        locale = getdefaultlocale()
        translator = QtCore.QTranslator(self.app)
        translator.load(os.path.join(self.current_dir, 'locale', 'qt_%s.qm' % locale[0]))
        self.app.installTranslator(translator)

        self.trayIcon = QtWidgets.QSystemTrayIcon()
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
    app.run()

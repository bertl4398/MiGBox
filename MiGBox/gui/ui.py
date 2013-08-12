# MiGBox Qt4 Graphical User Interface
#
# Copyright (C) 2013 Benjamin Ertl
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
MiGBox Qt4 Graphical User Interface.
Provides a GUI for the MiGBox synchronization.
"""

import os
import time
import threading
import logging

import paramiko

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from MiGBox.common import about, write_config, read_config, get_vars, print_vars
from MiGBox.sync import syncd
from MiGBox.mount import mount, unmount
from MiGBox.sftp import SFTPClient

# global variables' dictionary
_vars = {}
_key_pass = ''
_otp_user = ''
_otp_pass = ''

class SyncThread(QThread):
    """
    This class implements the thread that runs for synchronization,
    triggerd by the graphical user interface.
    """

    def __init__(self, parent=None):
        """
        Create a new C{QThread}.
        """

        super(SyncThread, self).__init__(parent)
        self.event = threading.Event()

    def sync(self, sftp):
        """
        Call C{start()} for this thread.

        Start synchronization.

        @param sftp: SFTP synchronization enabled or not
        @type sftp: bool
        """

        self.sftp = sftp
        self.start()

    def stop_sync(self):
        """
        Stop synchronization.

        Sets the event that the synchronization routine checks
        to terminate.
        """

        self.event.set()


    def run(self):
        mode = "remote" if self.sftp else "local"
        try:
            key = paramiko.RSAKey.from_private_key_file(_vars["KeyAuth"]["userkey"])
        except paramiko.PasswordRequiredException:
            dialog = _KeyPassUi(self)
            dialog.exec_()
        try:
            syncd.run(mode, username=_otp_user, password=_otp_pass, keypass=_key_pass,
                      stopsync=self.event, **get_vars(_vars))
        except Exception as e:
            self.emit(SIGNAL("threadError(QString)"), QString(e.message))

class _KeyPassUi(QDialog):
    """
    Class for the user's key password input dialog.
    """

    def __init__(self, parent=None):
        super(_KeyPassUi, self).__init__(parent)

        passLabel = QLabel("Password")
        self.passEdit = QLineEdit()
        self.passEdit.setEchoMode(QLineEdit.Password)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)

        layout = QVBoxLayout()
        layout.addWidget(passLabel)
        layout.addWidget(passEdit)
        self.setLayout(layout)
        self.setWindowTitle("MiGBox - User key password")

        self.connect(buttonBox, SIGNAL("accepted()"), self.accept)
        self.connect(buttonBox, SIGNAL("rejected()"), self.reject)

    def accept(self):
        global _key_pass
        _key_pass = str(self.passEdit.text())
        QDialog.accept(self)

class _OtpThread(QThread):
    """
    This class implements the thread that runs for generating one-time
    passwords, triggered by the graphical user interface.
    """

    def run(self):
        settings = get_vars(_vars)
        try:
            key = paramiko.RSAKey.from_private_key_file(_vars["KeyAuth"]["userkey"])
        except paramiko.PasswordRequiredException:
            dialog = _KeyPassUi(self)
            dialog.exec_()
        try:
            client = SFTPClient.connect(settings["sftp_host"], int(settings["sftp_port"]),
                                        settings["hostkey"], settings["userkey"], _key_pass,
                                        username=_otp_user, password=_otp_pass)
            client.onetimepass()
        except Exception as e:
            self.emit(SIGNAL("otpError(QString)"), QString(e.message))

class _OptionsUi(QDialog):
    """
    Class for app internal options dialog.
    """

    def __init__(self, parent=None):
        super(_OptionsUi, self).__init__(parent)

        urlLabel = QLabel("URL")
        self.urlEdit = QLineEdit(_vars["Connection"]["sftp_host"])

        portLabel = QLabel("Port")
        self.portEdit = QSpinBox()
        self.portEdit.setRange(0, 65535)
        port = _vars["Connection"]["sftp_port"]
        self.portEdit.setValue(int(port) if port else 0)

        pubKeyLabel = QLabel("Public key")
        self.pubKeyPathEdit = QLineEdit(_vars["KeyAuth"]["hostkey"])

        self.pubKeyPathButton = QPushButton("Path...")
        self.pubKeyPathButton.setToolTip("Path to the server's public key")

        serverGroupBox = QGroupBox("SFTP Server")
        serverBoxLayout = QGridLayout()
        serverBoxLayout.addWidget(urlLabel, 0, 0)
        serverBoxLayout.addWidget(self.urlEdit, 0, 1)
        serverBoxLayout.addWidget(portLabel, 1, 0)
        serverBoxLayout.addWidget(self.portEdit, 1, 1)
        serverBoxLayout.addWidget(pubKeyLabel, 2, 0)
        serverBoxLayout.addWidget(self.pubKeyPathEdit, 2, 1)
        serverBoxLayout.addWidget(self.pubKeyPathButton, 2, 2)
        serverGroupBox.setLayout(serverBoxLayout)

        usernameLabel = QLabel("Username")
        self.usernameEdit = QLineEdit()

        passwordLabel = QLabel("Password")
        self.passwordEdit = QLineEdit()
        self.passwordEdit.setEchoMode(QLineEdit.Password)

        prvKeyLabel = QLabel("Private key")
        self.prvKeyPathEdit = QLineEdit(_vars["KeyAuth"]["userkey"])

        self.prvKeyPathButton = QPushButton("Path...")
        self.prvKeyPathButton.setToolTip("Path to the user's private key")

        clientGroupBox = QGroupBox("SFTP Client")
        clientBoxLayout = QGridLayout()
        clientBoxLayout.addWidget(usernameLabel, 0, 0)
        clientBoxLayout.addWidget(self.usernameEdit, 0, 1)
        clientBoxLayout.addWidget(QLabel("(optional)"), 0, 2)
        clientBoxLayout.addWidget(passwordLabel, 1, 0)
        clientBoxLayout.addWidget(self.passwordEdit, 1, 1)
        clientBoxLayout.addWidget(QLabel("(optional)"), 1, 2)
        clientBoxLayout.addWidget(prvKeyLabel, 2, 0)
        clientBoxLayout.addWidget(self.prvKeyPathEdit, 2, 1)
        clientBoxLayout.addWidget(self.prvKeyPathButton, 2, 2)
        clientGroupBox.setLayout(clientBoxLayout)

        mountLabel = QLabel("Mount path")
        self.mountEdit = QLineEdit(_vars["Mount"]["mountpath"])

        self.mountPathButton = QPushButton("Path...")
        self.mountPathButton.setToolTip("Path to the mount point")

        mountGroupBox = QGroupBox("SFTP Mount")
        mountBoxLayout = QGridLayout()
        mountBoxLayout.addWidget(mountLabel, 0, 0)
        mountBoxLayout.addWidget(self.mountEdit, 0, 1)
        mountBoxLayout.addWidget(self.mountPathButton, 0, 2)
        mountGroupBox.setLayout(mountBoxLayout)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)

        layout = QVBoxLayout()
        layout.addWidget(serverGroupBox)
        layout.addWidget(clientGroupBox)
        layout.addWidget(mountGroupBox)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

        self.setWindowTitle("MiGBox - Options")

        self.connect(buttonBox, SIGNAL("accepted()"), self.accept)
        self.connect(buttonBox, SIGNAL("rejected()"), self.reject)
        self.connect(self.prvKeyPathButton, SIGNAL("clicked()"),
                     lambda: self._setPath(self.prvKeyPathEdit))
        self.connect(self.pubKeyPathButton, SIGNAL("clicked()"),
                     lambda: self._setPath(self.pubKeyPathEdit))
        self.connect(self.mountPathButton, SIGNAL("clicked()"), self._setMountPath)

    def accept(self):
        global _vars
        _vars["Connection"]["sftp_host"] = str(self.urlEdit.text())
        _vars["Connection"]["sftp_port"] = str(self.portEdit.value())
        _vars["KeyAuth"]["userkey"] = str(self.prvKeyPathEdit.text())
        _vars["KeyAuth"]["hostkey"] = str(self.pubKeyPathEdit.text())
        _vars["Mount"]["mountpath"] = str(self.mountEdit.text())
        global _otp_user
        global _otp_pass
        _otp_user = str(self.usernameEdit.text())
        _otp_pass = str(self.passwordEdit.text())
        QDialog.accept(self)

    def _setPath(self, lineEdit):
        path = QFileDialog.getOpenFileName(self, "MiGBox - Path to key file",
                                           lineEdit.text())
        if path:
            lineEdit.setText(QDir.toNativeSeparators(path))

    def _setMountPath(self):
        path = QFileDialog.getExistingDirectory(self, "MiGBox - Set Mount Path",
                                                self.mountEdit.text())
        if path:
            self.mountEdit.setText(QDir.toNativeSeparators(path))

class AppUi(QMainWindow):
    """
    MiGBox graphical user interface main window.
    """
    def __init__(self, configfile, logfile, icons_path, parent=None):
        super(AppUi, self).__init__(parent)

        self.configfile = configfile
        self.icons_path = icons_path
        self.isMount = False
        self.sftp = False

        global _vars

        srcPathLabel = QLabel("Source path")
        dstPathLabel = QLabel("Destination path")

        self.srcPathEdit = QLineEdit(_vars["Sync"]["source"])
        self.srcPathEdit.setToolTip("Source path for synchronization")

        self.dstPathEdit = QLineEdit (_vars["Sync"]["destination"])
        self.dstPathEdit.setToolTip("Destination path for synchronization")

        self.srcPathButton = QPushButton("Path...")
        self.srcPathButton.setToolTip("Sets the source path for synchronization")

        self.dstPathButton = QPushButton("Path...")
        self.dstPathButton.setToolTip("Sets the destination path for synchronization")

        self.remoteCheckBox = QCheckBox("&SFTP Server", self)
        self.remoteCheckBox.setFocusPolicy(Qt.NoFocus)
        self.remoteCheckBox.setToolTip("Connect to SFTP server")

        if not os.path.isfile(_vars["Logging"]["logfile"]):
            _vars["Logging"]["logfile"] = logfile
        with open(_vars["Logging"]["logfile"], 'wb') as f:
            f.write("New log file ...<br />")
 
        self.logBrowser = QTextBrowser()
        self.logBrowser.setLineWrapMode(QTextEdit.NoWrap)
        self.logBrowser.setSource(QUrl.fromLocalFile(_vars["Logging"]["logfile"]))

        self.logPathButton = QPushButton("Path")
        self.logPathButton.setToolTip("Set path to log file")
        self.logLevel = QComboBox(self)
        self.logLevel.addItem("INFO")
        self.logLevel.addItem("DEBUG")
        self.updateLogButton = QPushButton("&Update")
        self.updateLogButton.setToolTip("Update log")

        logLayout = QVBoxLayout()
        logLayout.addWidget(self.logBrowser)
        logOptionsLayout = QHBoxLayout()
        logOptionsLayout.addWidget(self.logPathButton)
        logOptionsLayout.addWidget(self.logLevel)
        logOptionsLayout.addWidget(self.updateLogButton)
        logLayout.addLayout(logOptionsLayout)

        logWidget = QWidget()
        logWidget.setLayout(logLayout)

        self.optionsButton = QPushButton("&Options")
        self.optionsButton.setToolTip("Configure MiGBox")

        self.syncButton = QPushButton("&Sync")
        self.syncButton.setToolTip("Start synchronization")

        self.stopButton = QPushButton("&Stop")
        self.stopButton.setToolTip("Stop synchronization")
        self.stopButton.setEnabled(False)

        gridLayout = QGridLayout()
        gridLayout.setSpacing(10)
        gridLayout.addWidget(srcPathLabel, 1, 0)
        gridLayout.addWidget(self.srcPathEdit, 1, 1)
        gridLayout.addWidget(self.srcPathButton, 1, 2)
        gridLayout.addWidget(dstPathLabel, 2, 0)
        gridLayout.addWidget(self.dstPathEdit, 2, 1)
        gridLayout.addWidget(self.dstPathButton, 2, 2)

        bottomLayout = QHBoxLayout()
        bottomLayout.addWidget(self.remoteCheckBox)
        bottomLayout.addWidget(self.optionsButton)
        bottomLayout.addStretch()
        bottomLayout.addWidget(self.syncButton)
        bottomLayout.addWidget(self.stopButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(gridLayout)
        mainLayout.addLayout(bottomLayout)

        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)

        self.srcTreeView = QTreeView()
        self.srcFsModel = QFileSystemModel(self.srcTreeView)
        self.srcFsModel.setRootPath(self.srcPathEdit.text())
        self.srcTreeView.setModel(self.srcFsModel)
        self.srcTreeView.setRootIndex(self.srcFsModel.index(self.srcPathEdit.text()))

        self.dstTreeView = QTreeView()
        self.dstFsModel = QFileSystemModel(self.dstTreeView)
        self.dstFsModel.setRootPath(self.dstPathEdit.text())
        self.dstTreeView.setModel(self.dstFsModel)
        self.dstTreeView.setRootIndex(self.dstFsModel.index(self.dstPathEdit.text()))

        self.aboutText = QPlainTextEdit(about)
        self.aboutText.setReadOnly(True)

        self.tabs = QTabWidget()
        self.tabs.addTab(mainWidget, "&Main")
        self.tabs.addTab(self.srcTreeView, "&Src Browser")
        self.tabs.addTab(self.dstTreeView, "&Dst Browser")
        self.tabs.addTab(logWidget, "&Log")
        self.tabs.addTab(self.aboutText, "&About")

        self.setCentralWidget(self.tabs)

        self.setWindowTitle("MiGBox - File Synchronization")

        exitAction = QAction(QIcon(os.path.join(icons_path, "exit.png")), "Exit MiGBox", self)
        exitAction.triggered.connect(self.close)
        trayAction = QAction(QIcon(os.path.join(icons_path, "tray.png")), "To tray", self)
        trayAction.triggered.connect(self._toTray)
        self.syncAction = QAction(QIcon(os.path.join(icons_path, "sync.png")),
                                  "Start synchronization", self)
        self.syncAction.triggered.connect(self._synchronize)
        self.stopAction = QAction(QIcon(os.path.join(icons_path, "stop.png")),
                                  "Stop synchronization", self)
        self.stopAction.triggered.connect(self._stopSynchronize)
        self.stopAction.setEnabled(False)
        self.mountAction = QAction(QIcon(os.path.join(icons_path, "mount.png")),
                                   "Mount sftp sync folder", self)
        self.mountAction.triggered.connect(self._mount)
        self.mountAction.setEnabled(False)
        self.otpAction = QAction(QIcon(os.path.join(icons_path, "otp.png")),
                                 "Create one-time-password", self)
        self.otpAction.triggered.connect(self._otp)
        self.otpAction.setEnabled(False)

        self.statusBar()
        toolbar = self.addToolBar("Toolbar")
        toolbar.addAction(exitAction)
        toolbar.addAction(trayAction)
        toolbar.addSeparator()
        toolbar.addAction(self.syncAction)
        toolbar.addAction(self.stopAction)
        toolbar.addSeparator()
        toolbar.addAction(self.mountAction)
        toolbar.addAction(self.otpAction)

        self.trayIcon = QSystemTrayIcon(QIcon(os.path.join(icons_path, "app.png")))
        self.trayMenu = QMenu()
        self.trayMenu.addAction(exitAction)
        restoreAction = QAction("Restore", self)
        restoreAction.triggered.connect(self._fromTray)
        self.trayMenu.addAction(restoreAction)
        self.trayMenu.addSeparator()
        self.trayMenu.addAction(self.syncAction)
        self.trayMenu.addAction(self.stopAction)
        self.trayMenu.addAction(self.mountAction)
        self.trayIcon.setContextMenu(self.trayMenu)

        self.thread = SyncThread()
        self.otpThread = _OtpThread()

        self.connect(self.otpThread, SIGNAL("otpError(QString)"), self._otpError)
        self.connect(self.logPathButton, SIGNAL("clicked()"), self._setLogPath)
        self.connect(self.thread, SIGNAL("finished()"), self._updateUi)
        self.connect(self.thread, SIGNAL("terminated()"), self._updateUi)
        self.connect(self.thread, SIGNAL("threadError(QString)"), self._syncError)
        self.connect(self.srcPathButton, SIGNAL("clicked()"), self._setSrcPath)
        self.connect(self.dstPathButton, SIGNAL("clicked()"), self._setDstPath)
        self.connect(self.remoteCheckBox, SIGNAL("stateChanged(int)"), self._setRemote)
        self.connect(self.optionsButton, SIGNAL("clicked()"), self._setOptions)
        self.connect(self.syncButton, SIGNAL("clicked()"), self._synchronize)
        self.connect(self.stopButton, SIGNAL("clicked()"), self._stopSynchronize)
        self.connect(self.updateLogButton, SIGNAL("clicked()"), self._refreshViews)
        self.connect(self.srcPathEdit, SIGNAL("textChanged(QString)"), self._saveSyncPaths)
        self.connect(self.dstPathEdit, SIGNAL("textChanged(QString)"), self._saveSyncPaths)
        self.connect(self.trayIcon, SIGNAL("activated(QSystemTrayIcon::ActivationReason)"),
                     self._handleSysTray)

    def closeEvent(self, event):
        # other cleanup?
        del(self.trayIcon)
        self._stopSynchronize()
        while self.thread.isRunning():
            time.sleep(0.1)
        write_config(self.configfile, _vars)
        if self.isMount:
            self._mount()
        event.accept()

    def _refreshViews(self):
        self.logBrowser.reload()
        self.logBrowser.moveCursor(QTextCursor.End)
        self.logBrowser.ensureCursorVisible() 
        self.srcTreeView.setModel(self.srcFsModel)
        self.srcTreeView.setRootIndex(self.srcFsModel.index(_vars["Sync"]["source"]))
        self.dstTreeView.setModel(self.dstFsModel)
        self.dstTreeView.setRootIndex(self.dstFsModel.index(_vars["Sync"]["destination"]))

    def _syncError(self, message):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("MiGBox - Sync Error")
        msgBox.setText("Synchronization failed.")
        msgBox.setInformativeText("""Check your settings:
- server is up and running
- server name/ip and port are valid
- server public key is valid
- user private/public key is valid
- keys have been exchanged and configured""")
        msgBox.setDetailedText(message)
        msgBox.exec_() 

    def _otpError(self, message):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("MiGBox - OTP Error")
        msgBox.setText("Could not create the one-time-password.")
        msgBox.setDetailedText(message)
        msgBox.exec_()

    def _otp(self):
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("MiGBox - One-Time-Password")
        msgBox.setText("You are about to create a One-Time-Password.")
        msgBox.setInformativeText("You want to proceed?")
        msgBox.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            self.otpThread.start()

    def _mount(self):
        host = _vars["Connection"]["sftp_host"] 
        port = _vars["Connection"]["sftp_port"]
        port = int(port) if port else 0
        userkey = _vars["KeyAuth"]["userkey"]
        mountpath = _vars["Mount"]["mountpath"]
        if not self.isMount:
            if not os.path.isdir(mountpath):
                msgBox = QMessageBox.warning(self, "MiGBox - Mount",
                    "Not a valid mount path.", QMessageBox.Ok)
            try:
                mount(host, port, userkey, mountpath)
                self.dstFsModel = QFileSystemModel(self.dstTreeView)
                self.dstFsModel.setRootPath(mountpath)
                self.dstTreeView.setModel(self.dstFsModel)
                self.dstTreeView.setRootIndex(self.dstFsModel.index(mountpath))
                self.mountAction.setIcon(QIcon(os.path.join(self.icons_path, "unmount.png")))
                self.mountAction.setToolTip(QString("Unmount sftp sync folder"))
                self.tabs.setTabEnabled(2, True)
                self.isMount = True
            except Exception as e:
                msgBox = QMessageBox(self)
                msgBox.setWindowTitle("MiGBox - SFTP Mount Error")
                msgBox.setText("Could not mount via SFTP.")
                msgBox.setDetailedText(e.message)
                msgBox.exec_()
        else:
            unmount(mountpath)
            self.tabs.setTabEnabled(2, False)
            self.mountAction.setIcon(QIcon(os.path.join(self.icons_path, "mount.png")))
            self.mountAction.setToolTip(QString("Mount sftp sync folder"))
            self.isMount = False

    def _toTray(self):
        self.hide()
        self.trayIcon.show()

    def _fromTray(self):
        self.show()
        self.activateWindow()
        self.trayIcon.hide()

    def _handleSysTray(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._fromTray()
        if reason == QSystemTrayIcon.Trigger:
            self.trayMenu.popup(QCursor.pos())

    def _saveSyncPaths(self):
        global _vars
        if self.remoteCheckBox.isChecked():
            _vars["Sync"]["source"] = str(self.srcPathEdit.text())
            _vars["Connection"]["sftp_host"] = str(self.dstPathEdit.text())
        else:
            _vars["Sync"]["source"] = str(self.srcPathEdit.text())
            _vars["Sync"]["destination"] = str(self.dstPathEdit.text())
        
    def _stopSynchronize(self):
        self.thread.stop_sync()
        self._updateUi()

    def _synchronize(self):
        global _vars
        if not os.path.isdir(_vars["Sync"]["source"]):
            msgBox = QMessageBox.warning(self, "MiGBox - Sync",
                "Not a valid source path.", QMessageBox.Ok)
        elif not self.sftp and not os.path.isdir(_vars["Sync"]["destination"]):
            msgBox = QMessageBox.warning(self, "MiGBox - Sync",
                "Not a valid destination path.", QMessageBox.Ok)
        else:
            _vars["Logging"]["loglevel"] = str(self.logLevel.currentText())
            self.srcPathButton.setEnabled(False)
            self.dstPathButton.setEnabled(False)
            self.optionsButton.setEnabled(False)
            self.syncButton.setEnabled(False)
            self.syncAction.setEnabled(False)
            self.logPathButton.setEnabled(False)
            self.logLevel.setEnabled(False)
            self.stopAction.setEnabled(True)
            self.stopButton.setEnabled(True)
            self.srcPathEdit.setReadOnly(True)
            self.dstPathEdit.setReadOnly(True)
            self.thread.event.clear()
            self.thread.sync(self.remoteCheckBox.isChecked())

    def _updateUi(self):
        self.srcPathButton.setEnabled(True)
        self.dstPathButton.setEnabled(True)
        self.optionsButton.setEnabled(True)
        self.syncButton.setEnabled(True)
        self.syncAction.setEnabled(True)
        self.logPathButton.setEnabled(True)
        self.logLevel.setEnabled(True)
        self.stopAction.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.srcPathEdit.setReadOnly(False)
        self.dstPathEdit.setReadOnly(False)

    def _setOptions(self):
        dialog = _OptionsUi(self)
        dialog.exec_()
        if self.remoteCheckBox.isChecked():
            self.dstPathEdit.setText(_vars["Connection"]["sftp_host"])

    def _setRemote(self, value):
        if self.remoteCheckBox.isChecked():
            self.dstPathEdit.setText(_vars["Connection"]["sftp_host"])
            self.dstPathButton.setVisible(False)
            self.tabs.setTabEnabled(2, False)
            self.mountAction.setEnabled(True)
            self.otpAction.setEnabled(True)
            self.sftp = True
        else:
            self.dstPathEdit.setText(_vars["Sync"]["destination"])
            self.dstPathButton.setVisible(True)
            self.tabs.setTabEnabled(2, True)
            self.mountAction.setEnabled(False)
            self.otpAction.setEnabled(False)
            self.sftp = False

    def _setLogPath(self):
        path = QFileDialog.getOpenFileName(self, "MiGBox - Path to key file",
                                           _vars["Logging"]["logfile"])
        if path:
            _vars["Logging"]["logfile"] = str(QDir.toNativeSeparators(path))
            self.logBrowser.setSource(QUrl.fromLocalFile(_vars["Logging"]["logfile"]))


    def _setSrcPath(self):
        path = QFileDialog.getExistingDirectory(self, "MiGBox - Set Source Path",
                                                self.srcPathEdit.text())
        if path:
            self.srcPathEdit.setText(QDir.toNativeSeparators(path))
            self.srcFsModel.setRootPath(self.srcPathEdit.text())
            self.srcTreeView.setRootIndex(self.srcFsModel.index(self.srcPathEdit.text()))
            self._saveSyncPaths()

    def _setDstPath(self):
        path = QFileDialog.getExistingDirectory(self, "MiGBox - Set Destination Path",
                                                self.dstPathEdit.text())
        if path:
            self.dstPathEdit.setText(QDir.toNativeSeparators(path))
            self.dstFsModel.setRootPath(self.dstPathEdit.text())
            self.dstTreeView.setRootIndex(self.dstFsModel.index(self.dstPathEdit.text()))
            self._saveSyncPaths()

    @classmethod
    def run(cls, configfile='', logfile='', icons_path=''):
        paramiko_logger = logging.getLogger("paramiko.transport")
        paramiko_logger.addHandler(logging.NullHandler())
        if not icons_path:
            # try to get icons from default location relative to this module
            # ../../icons
            icons_path = os.path.split(
                             os.path.split(
                                 os.path.split(os.path.abspath(__file__))[0])[0])[0]
            icons_path = os.path.join(icons_path, "icons")

        if not configfile:
            # write config in directory relative to this module
            configfile = os.path.join(os.path.split(os.path.abspath(__file__))[0], "migbox.cfg")
        if not logfile:
            # write log in directory relative to this module
            logfile = os.path.join(os.path.split(os.path.abspath(__file__))[0], "sync.log")

        app = QApplication([])
        app.setApplicationName("MiGBox")
        app.setWindowIcon(QIcon(os.path.join(icons_path, "app.png")))
        global _vars
        _vars = read_config(configfile)
        appUi = cls(configfile, logfile, icons_path)
        appUi.show()

        app.exec_()

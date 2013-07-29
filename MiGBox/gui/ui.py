#!/usr/bin/python
#
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
import sys
import threading

from ConfigParser import SafeConfigParser

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from MiGBox.common import ABOUT
from MiGBox.sync import syncd

class SyncThread(QThread):
    def __init__(self, parent=None):
        super(SyncThread, self).__init__(parent)

        self.event = threading.Event()

    def sync(self, sftp):
        self.sftp = sftp
        self.start()

    def run(self):
        settings = QSettings()

        src = str(settings.value("sync_src").toString())
        dst = str(settings.value("sync_dst").toString())
        host = str(settings.value("sftp_host").toString())
        port = int(settings.value("sftp_port").toInt()[0])
        hostkey = str(settings.value("hostkey").toString())
        userkey = str(settings.value("userkey").toString())
        log_file = str(settings.value("log_file").toString())
        log_level = str(settings.value("log_level").toString())

        mode = 'remote' if self.sftp else 'local'
        syncd.run(mode, src, dst, host, port, hostkey, userkey,
                  log_file, log_level, self.event)

    def stop_sync(self):
        self.event.set()

class OptionsUi(QDialog):
    def __init__(self, parent=None):
        super(OptionsUi, self).__init__(parent)

        settings = QSettings()

        # TODO validate sftp host url
        #urlRegExp = QRegExp("localhost|(\d{0,3}.\\d{0,3}.\\d{0,3}.\\d{0,3})")
        #urlValidator = QRegExpValidator(urlRegExp)

        urlLabel = QLabel("URL")
        self.urlEdit = QLineEdit(settings.value("sftp_host").toString())

        portLabel = QLabel("Port")
        self.portEdit = QSpinBox()
        self.portEdit.setRange(0, 65535)
        self.portEdit.setValue(settings.value("sftp_port").toInt()[0])

        pubKeyLabel = QLabel("Public key")
        self.pubKeyPathEdit = QLineEdit(settings.value("hostkey").toString())

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
        self.prvKeyPathEdit = QLineEdit(settings.value("userkey").toString())

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

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)

        layout = QVBoxLayout()
        layout.addWidget(serverGroupBox)
        layout.addWidget(clientGroupBox)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

        self.setWindowTitle("MiGBox - Options")

        self.connect(buttonBox, SIGNAL("accepted()"), self.accept)
        self.connect(buttonBox, SIGNAL("rejected()"), self.reject)
        self.connect(self.prvKeyPathButton, SIGNAL("clicked()"),
                     lambda: self._setPath(self.prvKeyPathEdit))
        self.connect(self.pubKeyPathButton, SIGNAL("clicked()"),
                     lambda: self._setPath(self.pubKeyPathEdit))

    def accept(self):
        settings = QSettings()
        settings.setValue("sftp_host", QVariant(self.urlEdit.text()))
        settings.setValue("sftp_port", QVariant(self.portEdit.value()))
        settings.setValue("userkey", QVariant(self.prvKeyPathEdit.text()))
        settings.setValue("hostkey", QVariant(self.pubKeyPathEdit.text()))

        QDialog.accept(self)

    def _setPath(self, lineEdit):
        path = QFileDialog.getOpenFileName(self, "MiGBox - Path to key file", lineEdit.text())
        if path:
            lineEdit.setText(QDir.toNativeSeparators(path))

class AppUi(QMainWindow):
    def __init__(self, configfile, icons_path):
        super(AppUi, self).__init__(None)

        self.configfile = configfile

        config = SafeConfigParser()
        config.read(configfile)
        settings = QSettings()
        settings.setValue("sync_src", str(config.get("Sync", "sync_src")))
        settings.setValue("sync_dst", str(config.get("Sync", "sync_dst")))
        settings.setValue("sftp_host", str(config.get("Connection", "sftp_host")))
        settings.setValue("sftp_port", int(config.getint("Connection", "sftp_port")))
        settings.setValue("hostkey", str(config.get("KeyAuth", "hostkey")))
        settings.setValue("userkey", str(config.get("KeyAuth", "userkey")))
        settings.setValue("log_file", str(config.get("Logging", "log_file")))
        settings.setValue("log_level", str(config.get("Logging", "log_level")))

        srcPathLabel = QLabel("Source path")
        dstPathLabel = QLabel("Destination path")

        self.srcPathEdit = QLineEdit(settings.value("sync_src").toString())
        self.srcPathEdit.setToolTip("Source path for synchronization")

        self.dstPathEdit = QLineEdit(settings.value("sync_dst").toString())
        self.dstPathEdit.setToolTip("Destination path for synchronization")

        self.srcPathButton = QPushButton("Path...")
        self.srcPathButton.setToolTip("Sets the source path for synchronization")

        self.dstPathButton = QPushButton("Path...")
        self.dstPathButton.setToolTip("Sets the destination path for synchronization")

        self.remoteCheckBox = QCheckBox("&SFTP Server")
        self.remoteCheckBox.setToolTip("Connect to SFTP server")

        logFile = settings.value("log_file").toString()

        self.logBrowser = QTextBrowser()
        self.logBrowser.setLineWrapMode(QTextEdit.NoWrap)
        self.logBrowser.setSource(QUrl(logFile))

        self.updateLogButton = QPushButton("&Update")
        self.updateLogButton.setToolTip("Update log")

        logLayout = QVBoxLayout()
        logLayout.addWidget(self.logBrowser)
        logLayout.addWidget(self.updateLogButton)

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

        self.aboutText = QPlainTextEdit(ABOUT)
        self.aboutText.setReadOnly(True)

        tabs = QTabWidget()
        tabs.addTab(mainWidget, "&Main")
        tabs.addTab(self.srcTreeView, "&Src Browser")
        tabs.addTab(self.dstTreeView, "&Dst Browser")
        tabs.addTab(logWidget, "&Log")
        tabs.addTab(self.aboutText, "&About")

        self.setCentralWidget(tabs)

        self.setWindowTitle("MiGBox - File Synchronization")

        exitAction = QAction(QIcon(os.path.join(icons_path, "exit.png")), "Exit", self)
        exitAction.triggered.connect(self.close)
        syncAction = QAction(QIcon(os.path.join(icons_path, "sync.png")),
                             "Start synchronization", self)
        syncAction.triggered.connect(self._synchronize)
        stopAction = QAction(QIcon(os.path.join(icons_path, "stop.png")),
                             "Stop synchronization", self)
        stopAction.triggered.connect(self._stopSynchronize)
        mountAction = QAction(QIcon(os.path.join(icons_path, "mount.png")),
                              "Mount sftp sync folder", self)
        mountAction.triggered.connect(self._toTray)

        self.statusBar()
        toolbar = self.addToolBar("Toolbar")
        toolbar.addAction(exitAction)
        toolbar.addSeparator()
        toolbar.addAction(syncAction)
        toolbar.addAction(stopAction)
        toolbar.addSeparator()
        toolbar.addAction(mountAction)

        self.trayIcon = QSystemTrayIcon(QIcon(os.path.join(icons_path, "app.svg")))

        self.thread = SyncThread()

        self.connect(self.thread, SIGNAL("finished()"), self._updateUi)
        self.connect(self.thread, SIGNAL("terminated()"), self._updateUi)
        self.connect(self.thread, SIGNAL("sync(int)"), self._updateUi)
        self.connect(self.srcPathButton, SIGNAL("clicked()"), self._setSrcPath)
        self.connect(self.dstPathButton, SIGNAL("clicked()"), self._setDstPath)
        self.connect(self.remoteCheckBox, SIGNAL("stateChanged(int)"), self._setRemote)
        self.connect(self.optionsButton, SIGNAL("clicked()"), self._setOptions)
        self.connect(self.syncButton, SIGNAL("clicked()"), self._synchronize)
        self.connect(self.stopButton, SIGNAL("clicked()"), self._stopSynchronize)
        self.connect(self.updateLogButton, SIGNAL("clicked()"), self.logBrowser.reload)
        self.connect(self.srcPathEdit, SIGNAL("textChanged(QString)"), self._saveSyncPaths)
        self.connect(self.dstPathEdit, SIGNAL("textChanged(QString)"), self._saveSyncPaths)
        self.connect(self.trayIcon, SIGNAL("activated(QSystemTrayIcon::ActivationReason)"),
                     self._handleSysTray)

    def closeEvent(self, event):
        # other cleanup?
        del(self.trayIcon)

        self._stopSynchronize()

        settings = QSettings()
        config = SafeConfigParser()
        config.read(self.configfile)
        config.set("Sync", "sync_src", str(settings.value("sync_src").toString()))
        config.set("Sync", "sync_dst", str(settings.value("sync_dst").toString()))
        config.set("Connection", "sftp_host", str(settings.value("sftp_host").toString()))
        config.set("Connection", "sftp_port", str(settings.value("sftp_port").toString()))
        config.set("KeyAuth", "hostkey", str(settings.value("hostkey").toString()))
        config.set("KeyAuth", "userkey", str(settings.value("userkey").toString()))
        config.set("Logging", "log_file", str(settings.value("log_file").toString()))
        config.set("Logging", "log_level", str(settings.value("log_level").toString()))
        with open(self.configfile, 'wb') as f:
            config.write(f)

        # event.ignore()
        event.accept()

    def _toTray(self):
        self.hide()
        self.trayIcon.show()

    def _handleSysTray(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()
            self.trayIcon.hide()

    def _saveSyncPaths(self):
        settings = QSettings()
        if self.remoteCheckBox.isChecked():
            settings.setValue("sync_src", str(self.srcPathEdit.text()))
            settings.setValue("sftp_host", str(self.dstPathEdit.text()))
        else:
            settings.setValue("sync_src", str(self.srcPathEdit.text()))
            settings.setValue("sync_dst", str(self.dstPathEdit.text()))
        
    def _stopSynchronize(self):
        self.thread.stop_sync()
        self._updateUi()

    def _synchronize(self):
        self.srcPathButton.setEnabled(False)
        self.dstPathButton.setEnabled(False)
        self.optionsButton.setEnabled(False)
        self.syncButton.setEnabled(False)
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
        self.stopButton.setEnabled(False)
        self.srcPathEdit.setReadOnly(False)
        self.dstPathEdit.setReadOnly(False)

    def _setOptions(self):
        dialog = OptionsUi(self)
        dialog.exec_()

    def _setRemote(self, value):
        settings = QSettings()
        if self.remoteCheckBox.isChecked():
            self.dstPathEdit.setText(settings.value("sftp_host").toString())
            self.dstPathButton.setVisible(False)
            self.dstTreeView.setModel(None)
        else:
            self.dstPathEdit.setText(settings.value("sync_dst").toString())
            self.dstPathButton.setVisible(True)
            self.dstTreeView.setModel(self.dstFsModel)
            self.dstTreeView.setRootIndex(self.dstFsModel.index(self.dstPathEdit.text()))

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

def run(configfile=None):
    if not configfile:
        # try to read from MIGBOXPATH environment variable
        if 'MIGBOXPATH' in os.environ:
            configfile = os.path.join(os.environ['MIGBOXPATH'], 'config/migbox.cfg')
            icons_path = os.path.join(os.environ['MIGBOXPATH'], 'icons')
        else:
            # try to read default location
            configfile = os.path.join(os.pardir, os.pardir, 'config/migbox.cfg')
            icons_path = os.path.join(os.pardir, os.pardir, 'icons')
    if not os.path.exists(configfile):
        print "Could not find configuration file!"
        sys.exit(1)
    if not os.path.exists(icons_path):
        print "Could not find application icons"
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("MiGBox")
    app.setWindowIcon(QIcon(os.path.join(icons_path, "app.svg")))

    appUi = AppUi(configfile, icons_path)
    appUi.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()

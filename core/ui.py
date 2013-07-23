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

__version__ = 0.3
__author__ = 'Benjamin Ertl'

ABOUT ="""\
MiGBox - File Synchronization for the Minimum Intrusion Grid (MiG)

Copyright (c) 2013 Benjamin Ertl

This program is free software; you can redistribute it and/or \
modify it under the terms of the GNU General Public License as \
published by the Free Software Foundation; either version 2 of \
the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, \
but WITHOUT ANY WARRANTY; without even the implied warranty of \
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the \
GNU General Public License for more details.

You should have received a copy of the GNU General Public License \
along with this program; if not, write to the Free Software \
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, \
MA 02110-1301 USA.
"""

import sys, os, threading
from ConfigParser import ConfigParser

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import syncd

CONFIGFILE = 'config.cfg'

def readConfig(filename=CONFIGFILE):
    config = ConfigParser()
    config.read(filename)

    settings = QSettings()
    for section in config.sections():
        for name, value in config.items(section):
            settings.setValue(name, value)

def writeConfig(filename, section, **kargs):
    config = ConfigParser()
    config.read(filename)
    for key in kargs:
        config.set(section, key, kargs[key] )
    
    with open(filename, "wb") as configfile:
            config.write(configfile)

class SyncThread(QThread):
    def __init__(self, parent=None):
        super(SyncThread, self).__init__(parent)

        self.event = threading.Event()

    def sync(self, sftp):
        self.sftp = sftp
        self.start()

    def run(self):
        syncd.main(self.sftp, self.event)

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
        self.urlEdit = QLineEdit(settings.value("sftp_host", QVariant("localhost")).toString())

        portLabel = QLabel("Port")
        self.portEdit = QSpinBox()
        self.portEdit.setRange(0, 65535)
        self.portEdit.setValue(settings.value("sftp_port", QVariant(50007)).toInt()[0])

        pubKeyLabel = QLabel("Public key")
        self.pubKeyPathEdit = QLineEdit(settings.value("srvkey", QVariant("test_rsa.pub")).toString())
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
        self.prvKeyPathEdit = QLineEdit(settings.value("prvkey", QVariant("user_rsa_key")).toString())
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
        self.connect(self.prvKeyPathButton, SIGNAL("clicked()"), \
                     lambda: self.setPath(self.prvKeyPathEdit))
        self.connect(self.pubKeyPathButton, SIGNAL("clicked()"), \
                     lambda: self.setPath(self.pubKeyPathEdit))

    def accept(self):
        settings = QSettings()
        settings.setValue("sftp_host", QVariant(self.urlEdit.text()))
        settings.setValue("sftp_port", QVariant(self.portEdit.value()))
        settings.setValue("prvkey", QVariant(self.prvKeyPathEdit.text()))
        settings.setValue("srvkey", QVariant(self.pubKeyPathEdit.text()))
        writeConfig(CONFIGFILE, "Connection", sftp_host=self.urlEdit.text(), \
                                              sftp_port=self.portEdit.value())
        writeConfig(CONFIGFILE, "KeyAuth", prvkey=self.prvKeyPathEdit.text(), \
                                           srvkey=self.pubKeyPathEdit.text())
        QDialog.accept(self)

    def setPath(self, lineEdit):
        path = QFileDialog.getOpenFileName(self, "MiGBox - Set path to key file", \
                                               lineEdit.text())
        if path:
            lineEdit.setText(QDir.toNativeSeparators(path))

class AppUi(QMainWindow):
    def __init__(self):
        super(AppUi, self).__init__(None)

        settings = QSettings()

        srcPathLabel = QLabel("Source path")
        dstPathLabel = QLabel("Destination path")

        srcPath = settings.value("sync_src", QVariant(os.getcwd())).toString()
        dstPath = settings.value("sync_dst", QVariant(os.getcwd())).toString()

        self.srcPathLabel = QLineEdit(srcPath)
        self.srcPathLabel.setToolTip("Source path for synchronization")

        self.dstPathLabel = QLineEdit(dstPath)
        self.dstPathLabel.setToolTip("Destination path for synchronization")

        self.srcPathButton = QPushButton("Path...")
        self.srcPathButton.setToolTip("Sets the source path")

        self.dstPathButton = QPushButton("Path...")
        self.dstPathButton.setToolTip("Sets the destination path")

        self.remoteCheckBox = QCheckBox("&SFTP Server")
        self.remoteCheckBox.setToolTip("Connect to  SFTP server")

        logFile = settings.value("log_file", QVariant("sync.log")).toString()

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
        gridLayout.addWidget(self.srcPathLabel, 1, 1)
        gridLayout.addWidget(self.srcPathButton, 1, 2)
        gridLayout.addWidget(dstPathLabel, 2, 0)
        gridLayout.addWidget(self.dstPathLabel, 2, 1)
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
        self.srcFsModel.setRootPath(self.srcPathLabel.text())
        self.srcTreeView.setModel(self.srcFsModel)
        self.srcTreeView.setRootIndex(self.srcFsModel.index(self.srcPathLabel.text()))

        self.dstTreeView = QTreeView()
        self.dstFsModel = QFileSystemModel(self.dstTreeView)
        self.dstFsModel.setRootPath(self.dstPathLabel.text())
        self.dstTreeView.setModel(self.dstFsModel)
        self.dstTreeView.setRootIndex(self.dstFsModel.index(self.dstPathLabel.text()))

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

        exitAction = QAction(QIcon("icons/exit.png"), "Exit", self)
        exitAction.triggered.connect(self.close)
        syncAction = QAction(QIcon("icons/sync.png"), "Start synchronization", self)
        syncAction.triggered.connect(self.synchronize)
        stopAction = QAction(QIcon("icons/stop.png"), "Stop synchronization", self)
        stopAction.triggered.connect(self.stopSynchronize)
        mountAction = QAction(QIcon("icons/mount.png"), "Mount sftp sync folder", self)

        self.statusBar()
        toolbar = self.addToolBar("Toolbar")
        toolbar.addAction(exitAction)
        toolbar.addSeparator()
        toolbar.addAction(syncAction)
        toolbar.addAction(stopAction)
        toolbar.addSeparator()
        toolbar.addAction(mountAction)

        self.thread = SyncThread()

        self.connect(self.thread, SIGNAL("finished()"), self.updateUi)
        self.connect(self.thread, SIGNAL("terminated()"), self.updateUi)
        self.connect(self.thread, SIGNAL("sync(int)"), self.updateUi)
        self.connect(self.srcPathButton, SIGNAL("clicked()"), self.setSrcPath)
        self.connect(self.dstPathButton, SIGNAL("clicked()"), self.setDstPath)
        self.connect(self.remoteCheckBox, SIGNAL("stateChanged(int)"), self.setRemote)
        self.connect(self.optionsButton, SIGNAL("clicked()"), self.setOptions)
        self.connect(self.syncButton, SIGNAL("clicked()"), self.synchronize)
        self.connect(self.stopButton, SIGNAL("clicked()"), self.stopSynchronize)
        self.connect(self.updateLogButton, SIGNAL("clicked()"), self.logBrowser.reload)
        self.connect(self.srcPathLabel, SIGNAL("textChanged(QString)"), self.saveSyncPaths)
        self.connect(self.dstPathLabel, SIGNAL("textChanged(QString)"), self.saveSyncPaths)

    def saveSyncPaths(self):
        if self.remoteCheckBox.isChecked():
            writeConfig(CONFIGFILE, "Sync", sync_src=self.srcPathLabel.text())
            writeConfig(CONFIGFILE, "Connection", sftp_host=self.dstPathLabel.text())
        else:
            writeConfig(CONFIGFILE, \
                        "Sync", sync_src=self.srcPathLabel.text(), \
                                sync_dst=self.dstPathLabel.text())
        
    def stopSynchronize(self):
        self.thread.stop_sync()
        self.updateUi()

    def synchronize(self):
        self.srcPathButton.setEnabled(False)
        self.dstPathButton.setEnabled(False)
        self.optionsButton.setEnabled(False)
        self.syncButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.srcPathLabel.setReadOnly(True)
        self.dstPathLabel.setReadOnly(True)
        self.thread.event.clear()
        self.thread.sync(self.remoteCheckBox.isChecked())

    def updateUi(self):
        self.srcPathButton.setEnabled(True)
        self.dstPathButton.setEnabled(True)
        self.optionsButton.setEnabled(True)
        self.syncButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.srcPathLabel.setReadOnly(False)
        self.dstPathLabel.setReadOnly(False)

    def setOptions(self):
        dialog = OptionsUi(self)
        dialog.exec_()

    def setRemote(self, value):
        settings = QSettings()
        if self.remoteCheckBox.isChecked():
            self.dstPathLabel.setText(settings.value("sftp_host", QVariant("localhost")).toString())
            self.dstPathButton.setVisible(False)
            self.dstTreeView.setModel(None)
        else:
            self.dstPathLabel.setText(settings.value("sync_dst", QVariant(os.getcwd())).toString())
            self.dstPathButton.setVisible(True)
            self.dstTreeView.setModel(self.dstFsModel)
            self.dstTreeView.setRootIndex(self.dstFsModel.index(self.dstPathLabel.text()))

    def setSrcPath(self):
        path = QFileDialog.getExistingDirectory(self, "MiGBox - Set Source Path", self.srcPathLabel.text())
        if path:
            self.srcPathLabel.setText(QDir.toNativeSeparators(path))
            self.srcFsModel.setRootPath(self.srcPathLabel.text())
            self.srcTreeView.setRootIndex(self.srcFsModel.index(self.srcPathLabel.text()))
            self.saveSyncPaths()

    def setDstPath(self):
        path = QFileDialog.getExistingDirectory(self, "MiGBox - Set Destination Path", self.dstPathLabel.text())
        if path:
            self.dstPathLabel.setText(QDir.toNativeSeparators(path))
            self.dstFsModel.setRootPath(self.dstPathLabel.text())
            self.dstTreeView.setRootIndex(self.dstFsModel.index(self.dstPathLabel.text()))
            self.saveSyncPaths()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("MiGBox")
    app.setWindowIcon(QIcon("icons/app.svg"))

    readConfig(CONFIGFILE)
    appUi = AppUi()
    appUi.show()

    sys.exit(app.exec_())

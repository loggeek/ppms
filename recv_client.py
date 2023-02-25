from PyQt5.QtCore import *
from PyQt5.QtGui import * 
from PyQt5.QtWidgets import * 

from sys import argv, exit
from socket import socket, AF_INET, SOCK_STREAM
from configparser import ConfigParser


def main():
    # QT App
    app = QApplication(argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Read config
    cfg = ConfigParser()
    cfg.read("config.ini", encoding='utf-8')
    
    # Parse config
    ip = cfg["client"]["ip"]
    port = int(cfg["client"]["port"])
    
    # Run client
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((ip, port))
        sock.send(b"DUMMY")
        message = sock.recv(1024)
        RecvWindow.main(message)
    finally:
        sock.close()
    
    exit(app.exec_())


class RecvWindow(object):
    def setupUi(self, dialog, message):
        # Create dialog
        dialog.setObjectName("dialog")
        dialog.setWindowTitle("Alerte")
        dialog.setWindowFlags(Qt.FramelessWindowHint) # Qt.WindowStaysOnTopHint

        self.verticalLayout = QVBoxLayout(dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        
        # Create items
        self.alertTextEdit = QPlainTextEdit(dialog)
        self.alertTextEdit.setObjectName("alertTextEdit")
        self.alertTextEdit.setPlainText(message.decode("utf-8"))
        self.alertTextEdit.setReadOnly(True)
        self.alertTextEdit.setStyleSheet("""QPlainTextEdit {
            background-color: #00F;
            color: #FFF;
            font-size: 36pt;
        }""")
        self.verticalLayout.addWidget(self.alertTextEdit)
        
        self.dismissButton = QPushButton(dialog)
        self.dismissButton.setObjectName("alertButton")
        self.dismissButton.setText("J'ai compris")
        self.dismissButton.clicked.connect(dialog.close)
        self.verticalLayout.addWidget(self.dismissButton)
        
        QMetaObject.connectSlotsByName(dialog)

    def main(message):
        dialog = QDialog()
        ui = RecvWindow()
        ui.setupUi(dialog, message)
        dialog.showFullScreen()
        dialog.exec_()


if __name__ == "__main__":
    main()

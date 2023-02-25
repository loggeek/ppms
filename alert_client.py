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

    # Get icon
    icon = QIcon("icon.png")

    # Adding item on the menu bar
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)
    
    # Set actions
    tray.activated.connect(
        lambda reason: activated(reason, app)
    )
    
    exit(app.exec_())


def activated(reason, app):
    # Verify the type of trigger
    if reason == QSystemTrayIcon.Trigger:
        AlertWindow.main()
    elif reason == QSystemTrayIcon.MiddleClick:
        option = QMessageBox.warning(
            None, "Attention", "Êtes-vous sûr(e) de vouloir quitter?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if option == QMessageBox.Yes:
            app.quit()


class AlertWindow(object):
    messages = {}

    def setupUi(self, Dialog):
        # Read config
        cfg = ConfigParser()
        cfg.read("config.ini", encoding='utf-8')
        
        # Parse config
        self.ip = cfg["client"]["ip"]
        self.port = int(cfg["client"]["port"])
        self.messages = {
            key.capitalize() : value.strip() for key, value in dict(cfg["messages"]).items()
        }
        
        # Create dialog
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 300)
        Dialog.setWindowTitle("Menu d'alerte")
        Dialog.setWindowIcon(QIcon("icon.png")); 

        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        
        # Create items
        self.presetsComboBox = QComboBox(Dialog)
        self.presetsComboBox.setObjectName("presetsComboBox")
        self.presetsComboBox.addItems(self.messages.keys())
        self.presetsComboBox.currentTextChanged.connect(
            lambda key: self.alertTextEdit.setPlainText(self.messages[key])
        )
        self.verticalLayout.addWidget(self.presetsComboBox)

        self.alertTextEdit = QPlainTextEdit(Dialog)
        self.alertTextEdit.setObjectName("alertTextEdit")
        self.alertTextEdit.setPlainText(self.messages[self.presetsComboBox.currentText()])
        self.verticalLayout.addWidget(self.alertTextEdit)

        self.alertButton = QPushButton(Dialog)
        self.alertButton.setObjectName("alertButton")
        self.alertButton.setText("Alerter")
        self.alertButton.clicked.connect(self.alert)
        self.verticalLayout.addWidget(self.alertButton)

        QMetaObject.connectSlotsByName(Dialog)

    def main():
        dialog = QDialog()
        ui = AlertWindow()
        ui.setupUi(dialog)
        dialog.show()
        dialog.exec_()

    def alert(self):
        message = self.alertTextEdit.toPlainText()
        
        # Run client
        try:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((self.ip, self.port))
            sock.send(str.encode(message))
            data = sock.recv(1024)
            if data == b"OK":
                QMessageBox.information(
                    None, "Information", "L'alerte a été envoyée", QMessageBox.Ok, QMessageBox.Ok
                )
            else:
                raise Exception
        except Exception as e:
            QMessageBox.warning(
                None, "Une erreur est survenue", "<code>{}</code".format(str(e)) , QMessageBox.Ok, QMessageBox.Ok
            )
        finally:
            sock.close()


if __name__ == "__main__":
    main()

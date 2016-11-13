# !/usr/bin/env python

from PyQt5.QtCore import Qt, QIODevice
from PyQt5.QtWidgets import QGridLayout, QLabel, QRadioButton, QTextEdit, QWidget, QTextBrowser, QPushButton, \
    QVBoxLayout, QLineEdit
from PyQt5.QtSerialPort import QSerialPort


class COMportMessenger(QWidget):
    def __init__(self, parent=None):
        super(COMportMessenger, self).__init__(parent)

        self.sender_name = "/dev/tnt1"
        self.receiver_name = "/dev/tnt0"

        # widget initialization
        input_label = QLabel("Input area:")
        self.input_text = QTextEdit()

        output_label = QLabel("Output area:")
        self.output_text = QTextBrowser()

        self.send_button = QPushButton()
        self.send_button.setText("Send")
        self.send_button.clicked.connect(self.handle_send_button)

        self.init_button = QPushButton()
        self.init_button.setText("Initialize")
        self.init_button.clicked.connect(self.handle_init_button)

        debug_label = QLabel("Debug info:")
        self.debug_text = QTextBrowser()

        self.button = QRadioButton("On - sender mode " + self.sender_name
                                   + ", off - receiver mode " + self.receiver_name)
        self.button.toggled.connect(self.handle_radio_button)

        # grid layout initialisation
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.button, 0, 0, Qt.AlignRight)
        grid_layout.addWidget(self.init_button, 0, 1, Qt.AlignCenter)
        grid_layout.addWidget(input_label, 1, 0, Qt.AlignHCenter)
        grid_layout.addWidget(self.input_text, 2, 0)
        grid_layout.addWidget(output_label, 1, 1, Qt.AlignHCenter)
        grid_layout.addWidget(self.output_text, 2, 1)
        grid_layout.addWidget(self.send_button, 3, 0)
        grid_layout.addWidget(debug_label, 4, 0)

        # debug info adding
        vbox_debug_text = QVBoxLayout()
        vbox_debug_text.addWidget(self.debug_text)

        # main layout
        main_layout = QGridLayout()
        main_layout.addLayout(grid_layout, 0, 0)
        main_layout.addLayout(vbox_debug_text, 1, 0)

        self.setLayout(main_layout)
        self.setWindowTitle("Simple COM port messenger")

        # serial port initialization
        self.com = QSerialPort()
        self.com.setBaudRate(QSerialPort.Baud115200)
        self.com.setDataBits(QSerialPort.Data8)
        self.com.setStopBits(QSerialPort.OneStop)
        self.com.setParity(QSerialPort.EvenParity)

    # sender/receiver mode switch
    def handle_radio_button(self):
        if self.button.isChecked():
            if self.com.isOpen():
                self.com.close()
            self.com.setPortName(self.sender_name)
            self.com.open(QIODevice.WriteOnly)
        else:
            if self.com.isOpen():
                self.com.close()
            self.com.setPortName(self.receiver_name)
            self.com.open(QIODevice.ReadOnly)

    # port initialization and opening
    def handle_init_button(self):
        if self.button.isChecked():
            self.com.setPortName(self.sender_name)
            self.com.open(QIODevice.WriteOnly)
        else:
            self.com.setPortName(self.receiver_name)
            self.com.readyRead.connect(self.handle_receive)
        self.debug_text.append("Port was initialized")

    # send message button handle
    def handle_send_button(self):
        if self.button.isChecked():
            text = self.input_text.toPlainText()
            self.com.writeData(bytes(text, 'utf8'))
            self.input_text.clear()

    # receive message button handle
    def handle_receive(self):
        if not self.button.isChecked():
            ba = self.com.readAll()
            string = str(ba, 'utf-8')
            self.output_text.append(string)


if __name__ == '__main__':
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    messenger = COMportMessenger()
    messenger.show()

    sys.exit(app.exec_())

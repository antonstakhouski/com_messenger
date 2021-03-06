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

        # special params for forming packets
        self.flag = "F"
        self.data_size = 7
        self.fcs = "9"
        self.escape = "E"
        self.flag_replacement = "R"
        self.not_flag_replacement = "N"
        self.placeholder = 0
        self.receiver_address = "0"

        # widget initialization
        input_label = QLabel("Input area:")
        self.input_text = QTextEdit()

        # set receiver/sender port
        self.com_pair_label = QLabel("Receiver address(1 byte)[For sender mode only]:")
        self.com_pair_text = QLineEdit("0")

        output_label = QLabel("Output area:")
        self.output_text = QTextBrowser()

        self.send_button = QPushButton()
        self.send_button.setText("Send")
        self.send_button.clicked.connect(self.handle_send_button)

        self.receive_button = QPushButton()
        self.receive_button.setText("Receive")
        self.receive_button.clicked.connect(self.handle_receive_button)

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
        grid_layout.addWidget(self.receive_button, 3, 1)
        grid_layout.addWidget(debug_label, 4, 0)

        # debug info adding
        vbox_debug_text = QVBoxLayout()
        vbox_debug_text.addWidget(self.debug_text)
        vbox_debug_text.addWidget(self.com_pair_label)
        vbox_debug_text.addWidget(self.com_pair_text)

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
            # self.com_pair_label = "Receiver port:"
            self.com.setPortName(self.sender_name)
            # self.com_pair_text = self.receiver_name
            self.com.open(QIODevice.WriteOnly)
        else:
            if self.com.isOpen():
                self.com.close()
            # self.com_pair_label = "Sender port:"
            self.com.setPortName(self.receiver_name)
            # self.com_pair_text = self.sender_name
            self.com.open(QIODevice.ReadOnly)

    # port initialization and opening
    def handle_init_button(self):
        if self.button.isChecked():
            self.com.setPortName(self.sender_name)
            self.com.open(QIODevice.WriteOnly)
            self.receiver_address = self.com_pair_text.text()[:1]
            self.receiver_name = self.receiver_name[:-1] + self.receiver_address
        else:
            self.com.setPortName(self.receiver_name)
            self.com.open(QIODevice.ReadOnly)
            self.sender_name = self.com_pair_text.text()
        self.debug_text.append("Port was initialized")

    def byte_stuffing_encapsulation(self, packet):
        i = 1
        length = len(packet)
        while i < length:
            if packet[i] == self.flag:
                packet = packet[:i] + packet[i:].replace(packet[i], self.escape + self.flag_replacement, 1)
                i += 2
                continue
            if packet[i] == self.escape:
                packet = packet[:i] + packet[i:].replace(packet[i], self.escape + self.not_flag_replacement, 1)
                i += 2
                continue
            i += 1
        return packet

    # send message button handle
    def handle_send_button(self):
        if self.button.isChecked():
            text = self.input_text.toPlainText()
            # form packets
            for i in range(0, len(text), self.data_size):
                # get first self.data_size symbols
                text_tmp = text[:self.data_size]
                packet = str(self.flag)
                packet += self.receiver_address
                packet += self.sender_name[-1:]
                # cut first self.data_size symbols
                text = text[self.data_size:]
                # add data
                packet += text_tmp
                # if we have least than self.data_size data
                # add self.placeholder to fit self.data_size len
                if len(text_tmp) < self.data_size:
                    i = len(text_tmp)
                    while i < self.data_size:
                        packet += str(chr(self.placeholder))
                        i += 1
                # add fcs
                packet += self.fcs
                self.debug_text.append(packet)
                packet = self.byte_stuffing_encapsulation(packet)
                self.debug_text.append(packet)
                # send packet
                self.debug_text.append(str(len(packet)))
                self.com.writeData(bytes(packet, 'utf8'))
            self.input_text.clear()

    # receive message button handle
    def handle_receive_button(self):
        if not self.button.isChecked():
            ba = self.com.readAll()
            string = str(ba, 'utf-8')
            self.debug_text.append(str(len(string)))
            if len(string) > 0:
                # remove first incomplete packet
                index = string.index(self.flag)
                string = string[index:]
                # get list of packages
                string_list = string.split(self.flag, len(string))
                megastring = str()

                for packet in string_list:
                    length = len(packet)
                    if length > 0:
                        # byte_stuffing_decapsulation
                        string = packet[0] + packet[1:].replace(self.escape + self.flag_replacement, self.flag, length)
                        string = \
                            string[0] + string[1:].replace(self.escape + self.not_flag_replacement, self.escape, length)
                        if string[0] == self.receiver_name[-1:]:
                            # cut off receiver, source, fcs
                            string = string[2:-1]
                            megastring += string
                self.output_text.append(megastring)


if __name__ == '__main__':
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    addressBook = COMportMessenger()
    addressBook.show()

    sys.exit(app.exec_())

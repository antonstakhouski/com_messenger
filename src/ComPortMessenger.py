import random
import time
from PyQt5.QtCore import Qt, QIODevice
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtWidgets import QWidget, QLabel, QTextEdit, QTextBrowser, QPushButton, QRadioButton, QGridLayout, \
    QVBoxLayout

CODING = 'utf8'


class ComPortMessenger(QWidget):
    def __init__(self, parent=None):
        super(ComPortMessenger, self).__init__(parent)

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

        self.radio_button = QRadioButton("On - sender mode " + self.sender_name
                                         + ", off - receiver mode " + self.receiver_name)
        self.radio_button.toggled.connect(self.handle_radio_button)

        # grid layout initialisation
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.radio_button, 0, 0, Qt.AlignRight)
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

        self.com = QSerialPort()
        self.serial_port_init()
        # collision window in millis
        self.collision_window = 50
        self.jam_signal_time = 25
        self.slot_time = int((self.collision_window + self.jam_signal_time) * 1.25)
        self.max_tries = 10
        self.jam_signal = bytes(str(chr(7)), CODING)
        self.escape_signal = bytes(str(chr(6)), CODING)
        self.previous_byte = int()
        self.output_string = str()
        self.try_counter = int()

    def serial_port_init(self):
        # serial port initialization
        self.com.setBaudRate(QSerialPort.Baud115200)
        self.com.setDataBits(QSerialPort.Data8)
        self.com.setStopBits(QSerialPort.OneStop)
        self.com.setParity(QSerialPort.EvenParity)

    # sender/receiver mode switch
    def handle_radio_button(self):
        # if sender mode is on
        if self.radio_button.isChecked():
            if self.com.isOpen():
                self.com.close()
            self.com.setPortName(self.sender_name)
            self.com.open(QIODevice.WriteOnly)
        # if receiver mode is on
        else:
            if self.com.isOpen():
                self.com.close()
            self.com.setPortName(self.receiver_name)
            self.com.open(QIODevice.ReadOnly)

    # port initialization and opening
    def handle_init_button(self):
        if self.radio_button.isChecked():
            self.com.setPortName(self.sender_name)
            self.com.open(QIODevice.WriteOnly)
        else:
            self.com.setPortName(self.receiver_name)
            self.com.open(QIODevice.ReadOnly)
            self.com.readyRead.connect(self.handle_receive)
        self.debug_text.append("Port was initialized")

    # send message button handle
    def handle_send_button(self):
        if self.radio_button.isChecked():
            text = self.input_text.toPlainText()
            self.input_text.clear()
            if len(text):
                self.send_message(text)

    def send_message(self, text):
        for symbol in text:
            self.try_counter = 0
            successful_transfer = False
            while not successful_transfer:
                # wait free channel
                while not (self.get_current_second() % 2):
                    time.sleep(1)
                self.com.writeData(bytes(symbol, CODING))
                # wait collision window
                time.sleep(self.collision_window / 1000.0)
                if not (self.get_current_second() % 2):
                    self.handle_collision()
                else:
                    successful_transfer = True
        self.com.writeData(self.escape_signal)

    def handle_collision(self):
        self.debug_text.append("x")
        self.com.writeData(self.jam_signal)
        self.try_counter += 1
        if self.try_counter > 10:
            self.output_text.append("Error. Number of tries expired")
            return
        # wait random delay
        k = min(self.try_counter, self.max_tries)
        random.seed()
        slot_count = random.randint(0, 2 ** k)
        time.sleep(slot_count * self.slot_time / 1000.0)

    @staticmethod
    def get_current_second():
        time_tuple = time.localtime(time.time())
        return time_tuple[5]

    # receive message handle
    def handle_receive(self):
        if not self.radio_button.isChecked():
            byte_array = bytes(self.com.readAll())
            self.output_string = ""
            self.receive_message(byte_array)

    def receive_message(self, byte_array):
        no_previous_byte = True
        for new_byte in byte_array:
            if new_byte == self.jam_signal[0]:
                no_previous_byte = True
                continue
            if new_byte == self.escape_signal[0]:
                if not no_previous_byte:
                    self.output_string += chr(self.previous_byte)
                no_previous_byte = True
            # if we have an ordinary byte
            else:
                if not no_previous_byte:
                    self.output_string += chr(self.previous_byte)
                else:
                    no_previous_byte = False
                self.previous_byte = new_byte
        self.output_text.append(self.output_string)

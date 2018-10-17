import sys
import socket
from functools import partial
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QDialog, QVBoxLayout, QGridLayout, QLabel,\
    QGroupBox, QMessageBox
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal
from settings import pin_names, pins_to_control
from protocol import SetPin, Response, CheckPins, CheckPinsResponse, from_binary

HOST = '192.168.0.103'
PORT = 8888

class Communicate(QThread):
    received = pyqtSignal(bytes)
    connection_interrupt = pyqtSignal()

    def __init__(self, message):
        self.message = message
        self.HOST = HOST
        self.PORT = PORT
        super().__init__()

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((HOST, PORT))
                s.sendall(self.message)
                data = s.recv(1024)
                self.received.emit(data)
            except socket.error:
                self.connection_interrupt.emit()

class Client(QDialog):
    def __init__(self):
        super().__init__()
        self.HOST = '192.168.0.103'
        self.PORT = 8888
        self.title = 'RaspberryPi Controll'
        self.left = 500
        self.top = 500
        self.width = 500
        self.height = 500
        self.threads = []
        self.bulb_image_off = QPixmap('images/pin_off.png')
        self.bulb_image_on = QPixmap('images/pin_on.png')
        self.initUI()
        self.refresh_pin_statuses()

    def parse_response(self, data):
        response = from_binary(data)
        print('Received: {}'.format(response))
        if isinstance(response, Response):
            if response.success:
                self.statuses[response.pin] = response.state
                self.bulbs[response.pin].setPixmap(self.bulb_image_on if response.state else self.bulb_image_off)

    def connection_problem(self):
        print('Problem occured while connecting with {}:{}'.format(self.HOST, self.PORT))
        QMessageBox.information(self, 'Connection interrupted', "Problem occured while accessing {}:{}".format(self.HOST, self.PORT))

    def communicate_with_server(self, message):
        thread = Communicate(message)
        thread.connection_interrupt.connect(self.connection_problem)
        thread.received.connect(self.parse_response)
        thread.start()
        self.threads.append(thread)

    def refresh_pin_statuses(self):
        response = self.communicate_with_server(CheckPins().get_binary())
        if isinstance(response, CheckPinsResponse):
            for pin, bulb in zip(response.statuses, self.bulbs):
                bulb.setPixmap(self.bulb_image_on) if pin else bulb.setPixmap(self.bulb_image_off)
            self.statuses = response.statuses

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.createGridLayout()

        windowLayout = QVBoxLayout()
        windowLayout.addWidget(self.horizontalGroupBox)
        self.setLayout(windowLayout)

        self.show()

    def createGridLayout(self):
        self.horizontalGroupBox = QGroupBox("Connected to {}:{}".format(self.HOST, self.PORT))
        layout = QGridLayout()
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)
        layout.setColumnStretch(4, 1)
        layout.setColumnStretch(5, 1)
        layout.setColumnStretch(6, 1)
        layout.setColumnStretch(7, 1)
        layout.setColumnStretch(8, 1)

        pin_image_raw = QPixmap('images/pin.png')
        pin_image_rotated_raw = QPixmap('images/pin_rotated.png')

        self.bulbs = []

        for i in range(40):
            pin_name = "PIN{}".format(i+1) if (i+1) not in pin_names.keys() else pin_names[i+1]

            if i%2 == 1:
                button_column = 7
                bulb_column = 6
                name_column = 5
                picture_column = 4
                pin_image = pin_image_rotated_raw
            else:
                button_column = 0
                bulb_column = 1
                name_column = 2
                picture_column = 3
                pin_image = pin_image_raw

            row = i//2

            image_label = QLabel()
            image_label.setPixmap(pin_image)
            bulb_label = QLabel()
            bulb_label.setPixmap(self.bulb_image_off)
            self.bulbs.append(bulb_label)

            layout.addWidget(bulb_label, row, bulb_column)
            if (i+1) in pins_to_control:
                toggle_button = QPushButton('Toggle')
                toggle_button.clicked.connect(partial(self.toggle_pin, i+1))
                layout.addWidget(toggle_button, row, button_column)
            layout.addWidget(QLabel(pin_name), row, name_column)
            layout.addWidget(image_label, row, picture_column)

        self.horizontalGroupBox.setLayout(layout)

    def toggle_pin(self, pin):
        set_pin_to_high = not self.statuses[pin-1]
        control_pin = SetPin(pin, set_pin_to_high).get_binary()
        self.communicate_with_server(control_pin)

app = QApplication(sys.argv)
ex = Client()
sys.exit(app.exec_())
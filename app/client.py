import sys
import socket
from functools import partial

from PyQt5.QtWidgets import (
    QApplication,
    QPushButton,
    QDialog,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QGroupBox,
    QMessageBox,
)
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import QThread, pyqtSignal

from settings import pin_names, pins_to_control, HOST, PORT
from protocol import SetPin, Response, CheckPins, CheckPinsResponse, from_binary


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
                s.connect((self.HOST, self.PORT))
                s.sendall(self.message)
                data = s.recv(1024)
                self.received.emit(data)
            except socket.error:
                self.connection_interrupt.emit()


class Client(QDialog):
    def __init__(self):
        super().__init__()
        self.HOST = HOST
        self.PORT = PORT
        self.title = "RaspberryPi Control"
        self.left = 500
        self.top = 500
        self.width = 500
        self.height = 500
        self.threads = {}
        self.bulb_image_off = QPixmap("images/pin_off.png")
        self.bulb_image_on = QPixmap("images/pin_on.png")
        self.spinner = QMovie("images/spinner.gif")
        self.spinner.start()
        self.init_ui()
        self.refresh_pin_statuses()

    def parse_response(self, data):
        response = from_binary(data)
        print("Received: {}".format(response))
        if isinstance(response, Response):
            if response.success:
                self.statuses[response.pin - 1] = response.state
                self.bulbs[response.pin - 1].setPixmap(
                    self.bulb_image_on if response.state else self.bulb_image_off
                )
                self.toggle_buttons[response.pin - 1].setEnabled(True)
        if isinstance(response, CheckPinsResponse):
            for pin, bulb in zip(response.statuses, self.bulbs):
                bulb.setPixmap(self.bulb_image_on) if pin else bulb.setPixmap(
                    self.bulb_image_off
                )
            self.statuses = response.statuses
            for button in self.toggle_buttons.values():
                button.setEnabled(True)

    def connection_problem(self):
        print(
            "Problem occured while connecting with {}:{}".format(self.HOST, self.PORT)
        )
        QMessageBox.information(
            self,
            "Connection interrupted",
            "Problem occured while accessing {}:{}".format(self.HOST, self.PORT),
        )

    def communicate_with_server(self, message):
        thread = Communicate(message)
        self.threads[id(thread)] = thread
        thread.connection_interrupt.connect(self.connection_problem)
        thread.received.connect(self.parse_response)
        thread.finished.connect(partial(self.delete_thread, id(thread)))
        thread.start()

    def delete_thread(self, id):
        del self.threads[id]

    def refresh_pin_statuses(self):
        self.communicate_with_server(CheckPins().get_binary())

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.create_grid_layout()

        window_layout = QVBoxLayout()
        window_layout.addWidget(self.horizontalGroupBox)
        self.setLayout(window_layout)

        self.show()

    def create_grid_layout(self):
        self.horizontalGroupBox = QGroupBox(
            "Connected to {}:{}".format(self.HOST, self.PORT)
        )
        layout = QGridLayout()
        layout.setSpacing(0)
        layout.setColumnStretch(1, 0)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 0)
        layout.setColumnStretch(4, 1)
        layout.setColumnStretch(5, 0)
        layout.setColumnStretch(6, 0)
        layout.setColumnStretch(7, 1)
        layout.setColumnStretch(8, 1)

        pin_image_raw = QPixmap("images/pin.png")
        pin_image_rotated_raw = QPixmap("images/pin_rotated.png")

        self.bulbs = []
        self.toggle_buttons = {}

        for i in range(40):
            pin_name = (
                "PIN{}".format(i + 1)
                if (i + 1) not in pin_names.keys()
                else pin_names[i + 1]
            )

            if i % 2 == 1:
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

            row = i // 2

            image_label = QLabel()
            image_label.setPixmap(pin_image)
            bulb_label = QLabel()
            bulb_label.setPixmap(self.bulb_image_off)
            self.bulbs.append(bulb_label)

            layout.addWidget(bulb_label, row, bulb_column)
            if (i + 1) in pins_to_control:
                toggle_button = QPushButton("Toggle")
                toggle_button.clicked.connect(partial(self.toggle_pin, i + 1))
                self.toggle_buttons[i] = toggle_button
                layout.addWidget(toggle_button, row, button_column)
                toggle_button.setEnabled(False)
            layout.addWidget(QLabel(pin_name), row, name_column)
            layout.addWidget(image_label, row, picture_column)

        self.horizontalGroupBox.setLayout(layout)

    def toggle_pin(self, pin):
        self.toggle_buttons[pin - 1].setEnabled(False)
        self.bulbs[pin - 1].setMovie(self.spinner)
        set_pin_to_high = not self.statuses[pin - 1]
        control_pin = SetPin(pin, set_pin_to_high).get_binary()
        self.communicate_with_server(control_pin)


app = QApplication(sys.argv)
ex = Client()
sys.exit(app.exec_())

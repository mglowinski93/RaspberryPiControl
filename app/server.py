import asyncio

import RPi.GPIO as GPIO

from settings import pins_to_control
from protocol import from_binary, SetPin, Response, CheckPins, CheckPinsResponse


class EchoServerClientProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peer_name = transport.get_extra_info("peername")
        print("Connection from {}".format(peer_name))
        self.transport = transport

    def data_received(self, data):
        message = from_binary(data)
        if isinstance(message, SetPin):  # compare classes
            pin = message.pin
            state = message.state
            if pin in pins_to_control:
                GPIO.output(pin, GPIO.HIGH) if state else GPIO.output(pin, GPIO.LOW)
                response = Response(pin, state, True)
            else:
                response = Response(pin, state, False)

        if isinstance(message, CheckPins):
            response_list = []
            for i in range(1, 41):
                if i in pins_to_control:
                    response_list.append(GPIO.input(i))
                else:
                    response_list.append(0)
            response = CheckPinsResponse(response_list)

        print("Send to client: {}".format(response))
        self.transport.write(response.get_binary())
        self.transport.close()


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
for pin in pins_to_control:
    GPIO.setup(pin, GPIO.OUT)

loop = asyncio.get_event_loop()
# Each client connection will create a new protocol instance
coro = loop.create_server(EchoServerClientProtocol, "0.0.0.0", 8888)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
print("Serving on {}".format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()

import asyncio
import sys

from protocol import SetPin, Response, from_binary
from settings import HOST, PORT

pin_number = int(sys.argv[1])
pin_status = int(sys.argv[2])


class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, message, loop):
        self.message = message
        self.loop = loop

    def connection_made(self, transport):
        transport.write(self.message)
        print("Data sent: {!r}".format(self.message))

    def data_received(self, data):
        response = from_binary(data)
        if isinstance(response, Response):
            print("Command: Set Pin command")
            print("Pin: {}".format(response.pin))
            print("Success: {}".format(response.state))

    def connection_lost(self, exc):
        print("The server closed the connection")
        print("Stop the event loop")
        self.loop.stop()


loop = asyncio.get_event_loop()
message = SetPin(pin_number, pin_status).get_binary()
coro = loop.create_connection(lambda: EchoClientProtocol(message, loop), HOST, PORT)
loop.run_until_complete(coro)
loop.run_forever()
loop.close()

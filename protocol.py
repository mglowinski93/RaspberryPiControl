from enum import IntEnum
import struct, json

SET_PIN = 'SET_PIN'
RESPONSE_PIN = 'RESPONSE_PIN'
CHECK_PINS_STATUS = 'CHECK_PINS_STATUS'
CHECK_PINS_RESPONSE = 'CHECK_PINS_RESPONSE'

class Message():
    def __init__(self, *args):
        for arg, field in zip(args, self.fields):
            setattr(self, field, arg)

    @classmethod
    def from_dict(cls, d):
        argument_list = [d[field] for field in cls.fields]
        return cls(*argument_list)

    def get_binary(self):
        data_dict = {}
        for field in self.fields:
            data_dict[field] = getattr(self, field)
        data_dict["MessageType"] = self.message_type
        return json.dumps(data_dict).encode('utf-8')


class SetPin(Message):
    message_type = SET_PIN
    fields = ['pin', 'state']

    def __str__(self):
        return "set pin {} to {}".format(self.pin, self.state)

class Response(Message):
    message_type = RESPONSE_PIN
    fields = ['pin', 'state', 'success']

    def __str__(self):
        if self.success:
            message = "Pin {} was set to {}".format(self.pin, self.state)
        else:
            message = "Pin {} was not set to {}".format(self.pin, self.state)
        return message

class CheckPins(Message):
    message_type = CHECK_PINS_STATUS
    fields = []

class CheckPinsResponse(Message):
    message_type = CHECK_PINS_RESPONSE
    fields = ['statuses']

command_dict = {
    SET_PIN: SetPin,
    RESPONSE_PIN: Response,
    CHECK_PINS_STATUS: CheckPins,
    CHECK_PINS_RESPONSE: CheckPinsResponse,
}

def from_binary(data):
    response = json.loads(data.decode())
    return command_dict[response['MessageType']].from_dict(response)
import inspect
import logging
import os
import time
from enum import Enum

import numpy as np
import serial
from crc import CrcCalculator, Configuration

ANDROID_CONTROLLER_DIR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))


class ControllerType(Enum):
    HEAD = os.path.join(ANDROID_CONTROLLER_DIR_PATH, "head_spec.txt")
    ANDROID = os.path.join(ANDROID_CONTROLLER_DIR_PATH, "android_spec.txt")


class AndrController:
    def __init__(self, usb_port, steps=20, pause=0.1, controller_type=ControllerType.HEAD, spec=None):

        self.connected = False
        self.usb_port = usb_port
        self.default_steps = steps
        self.default_pause = pause
        self.controller_type = controller_type

        self.crc_prefix = '30 0E'
        self.crc_prefix_android = '30 34'  # 52 axis for android
        self.send_prefix = '5A' + ' ' + self.crc_prefix
        self.send_prefix_android = '5A' + ' ' + self.crc_prefix_android
        self.send_suffix = '5A 39 00 03 90 0C A5'
        self.turn_off_hexstring = '5A 15 C1 CF A5'
        self.turn_on_hexstring = '5A 1A 81 cb A5'

        if spec is not None:
            self.actuators, self.startup_values = self.read_spec(spec)
            print("\n\nCreate controller with spec: " + spec + "\n\n")
        else:
            self.actuators, self.startup_values = self.read_spec(controller_type.value)
            print("\n\nCreate controller with spec: " + controller_type.value + "\n\n")

        self.last_values = self.startup_values
        # CRC-16-IBM also called CRC-16/ARC
        crc_conf = Configuration(
            width=16,
            polynomial=0x8005,
            init_value=0x0000,
            final_xor_value=0x0000,
            reverse_input=True,
            reverse_output=True
        )
        self.crc_calculator = CrcCalculator(crc_conf, table_based=True)

    def read_spec(self, path):
        if path == '':
            return [], []
        with open(path) as f:
            lines = f.readlines()
        actuators = []
        startup_vals = []
        for i, l in enumerate(lines):
            if i == 0 or l.startswith('#'):
                continue
            parts = l.split(', ')
            actuators.append({'idx': int(parts[0]), 'short': parts[1], 'name': parts[2], 'init': int(parts[3]), 'group': parts[4]})
            startup_vals.append(int(parts[3]))
        return actuators, startup_vals

    def connect(self):
        try:
            self.connected = True
            self.serial_connection = serial.Serial(port=self.usb_port, baudrate=500000, timeout=0.3)
        except serial.SerialException:
            logging.error("AndrController: could not initialize connection!")
            self.connected = False
        return self.connected

    def __del__(self):
        if (self.connected):
            logging.info('closing usb connection')
            self.connected = False
            self.serial_connection.close()

    def disconnect(self):
        if (self.connected):
            self.connected = False
            self.serial_connection.close()

    def pressure_off(self):
        send_bytes = bytes.fromhex(self.turn_off_hexstring)
        _ = self.serial_connection.write(send_bytes)
        response = self.serial_connection.read(28)
        return response

    def pressure_on(self):
        send_bytes = bytes.fromhex(self.turn_on_hexstring)
        _ = self.serial_connection.write(send_bytes)
        response = self.serial_connection.read(28)
        return response

    def calculate_hex_checksum(self, byte_values):
        checksum = self.crc_calculator.calculate_checksum(byte_values)
        hex_checksum = hex(checksum).split('x')[-1].zfill(4)
        cs_1 = hex_checksum[:2]
        cs_2 = hex_checksum[2:]
        hex_checksum = cs_2 + cs_1
        return hex_checksum

    def send_values(self, values):
        assert len(values) == len(self.actuators)
        assert self.connected == True
        values = [v if v is not None else self.last_values[i] for i, v in enumerate(values)]
        hex_values = [hex(max(0, min(v, 255))).split('x')[-1].zfill(2) for v in values]
        hex_string = ' '.join(hex_values)
        byte_values = bytes.fromhex(self.crc_prefix + hex_string)
        hex_checksum = self.calculate_hex_checksum(byte_values)
        send_string = self.send_prefix + ' ' + hex_string + ' ' + hex_checksum + ' ' + self.send_suffix
        if len(self.actuators) == 52:  # android, not head
            byte_values = bytes.fromhex(self.crc_prefix_android + hex_string)
            hex_checksum = self.calculate_hex_checksum(byte_values)
            send_string = self.send_prefix_android + ' ' + hex_string + ' ' + hex_checksum + ' ' + self.send_suffix
        logging.debug('Sending', send_string)
        send_bytes = bytes.fromhex(send_string)
        bytes_sent = self.serial_connection.write(send_bytes)
        logging.debug('Sent', bytes_sent, 'bytes')
        response = self.serial_connection.read(28)
        logging.debug('Response:', response.hex())
        self.last_values = values
        return send_bytes, response

    def interpolate(self, v1, v2, steps=None):
        v1 = np.asarray(v1)
        v2 = np.asarray(v2)
        if steps is None:
            steps = self.default_steps
        ratios = np.linspace(0, 1, num=steps)
        vectors = list()
        for ratio in ratios:
            v = (1.0 - ratio) * v1 + ratio * v2
            vectors.append(np.rint(v).astype(int))
        return vectors

    def move_to(self, values, steps=None, pause=None):
        if pause is None:
            pause = self.default_pause
        vectors = self.interpolate(self.last_values, values, steps=steps)
        response = None
        send_bytes = None
        for v in vectors:
            send_bytes, response = self.send_values(v)
            time.sleep(pause)
        return send_bytes, response


class FakeAndrController(AndrController):

    def __init__(self, usb_port, steps=20, pause=0.1, controller_type=ControllerType.HEAD, spec=None):
        super().__init__(usb_port, steps, pause, controller_type, spec)


    def __del__(self):
        if (self.connected):
            self.connected = False

    def pressure_off(self):
        pass

    def pressure_on(self):
        pass

    def connect(self):
        self.connected = True
        self.serial_connection = FakeSerial()
        print('connected')

        return True

    def disconnect(self):
        if (self.connected):
            self.serial_connection.close()
            self.connected = False
            print("Device is disconnected.")

    def send_values(self, values):
        sent_values, _ = super().send_values(values)
        return sent_values, 'fake connections do not respond'


class FakeSerial(serial.Serial):
    def close(self):
        pass

    def write(self, data):
        pass

    def read(self, size=28):
        response = bytes(source=size)
        return response

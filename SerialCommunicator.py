import glob
import time

import serial

class SerialCommunicator:

    def __init__(self, colors=None):
        port = (glob.glob('/dev/cu.usbmodem*'))[0]
        self.ser = serial.Serial(port, 115200)
        self.colors = colors if colors != None else [0, 2, 4, 6, 9, 13, 17, 22, 28, 34, 43, 53, 65, 77, 89, 102, 115, 145, 195, 255]
        self.options = len(self.colors)
        self.colors.append(self.colors[-1])

        self.setup()

    def setup(self):
        confirmed = False
        while not confirmed:
            self.ser.write(int(1).to_bytes(1,byteorder='big'))
            time.sleep(1)
            print("write")
            while self.ser.in_waiting > 0:
                print("read")
                self.ser.read()
                print("confirmed")
                confirmed = True
        time.sleep(1)

    def send_colors(self, red, green, blue):
        r = self.determine_color_values(red)
        g = self.determine_color_values(green)
        b = self.determine_color_values(blue)

        while self.ser.in_waiting > 0:
            self.ser.read()

        for byte in r:
            self.ser.write(byte.to_bytes(1,byteorder='big'))
        while self.ser.in_waiting == 0:
            time.sleep(0.0001)
        while self.ser.in_waiting > 1:
            self.ser.read()
        res = int.from_bytes(self.ser.read(), byteorder='big')
        if res == 1:
            return

        for byte in g:
            self.ser.write(byte.to_bytes(1,byteorder='big'))
        while self.ser.in_waiting == 0:
            time.sleep(0.0001)
        while self.ser.in_waiting > 1:
            self.ser.read()
        res = int.from_bytes(self.ser.read(), byteorder='big')
        if res == 1:
            return

        for byte in b:
            self.ser.write(byte.to_bytes(1,byteorder='big'))
        while self.ser.in_waiting == 0:
            time.sleep(0.0001)
        while self.ser.in_waiting > 0:
            self.ser.read()

    def send_color(self, red, green, blue):
        r = self.determine_color_value(red)
        g = self.determine_color_value(green)
        b = self.determine_color_value(blue)

        while self.ser.in_waiting > 0:
            self.ser.read()

        self.ser.write(r.to_bytes(1,byteorder='big'))
        self.ser.write(g.to_bytes(1,byteorder='big'))
        self.ser.write(b.to_bytes(1,byteorder='big'))

        while self.ser.in_waiting == 0:
            time.sleep(0.0001)
        while self.ser.in_waiting > 0:
            self.ser.read()


    def determine_color_values(self, proportions):
        return [self.colors[int(prop*self.options)] for prop in proportions]

    def determine_color_value(self, proportion):
        return self.colors[int(proportion*self.options)]

import glob
import time
from queue import Queue

import serial
from screen import ScreenVisual

class SerialCommunicator:

    def __init__(self, colors=None):
        self.ser = None
        self.ser2 = None
        self.screen = None
        self.queue = None

        try:
            port = (glob.glob('/dev/cu.usbmodem*'))[0]
            self.ser = serial.Serial(port, 115200)
        except:
            print("No serial device found, display to screen")
        
        if self.ser is not None:
            try:
                port2 = (glob.glob('/dev/cu.usbserial*'))[0]
                self.ser2 = serial.Serial(port2, 115200)
            except:
                pass

        if self.ser is None:
            self.screen = ScreenVisual()

        self.colors = colors if colors != None else [0, 2, 4, 6, 9, 13, 17, 22, 28, 34, 43, 53, 65, 77, 89, 102, 115, 145, 195, 255]
        self.options = len(self.colors)
        self.colors.append(self.colors[-1])

        if self.ser2 is not None:
            self.setup2()
        elif self.ser is not None:
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
        if self.ser is None:
            self.queue.put((red, green, blue))
            return

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


    def send_color2(self, red, green, blue, red2, green2, blue2):
        if self.ser2 is None:
            self.send_color(red, green, blue)
            return
        
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

        r2 = self.determine_color_value(red2)
        g2 = self.determine_color_value(green2)
        b2 = self.determine_color_value(blue2)

        while self.ser2.in_waiting > 0:
            self.ser2.read()

        self.ser2.write(r2.to_bytes(1,byteorder='big'))
        self.ser2.write(g2.to_bytes(1,byteorder='big'))
        self.ser2.write(b2.to_bytes(1,byteorder='big'))

        while self.ser2.in_waiting == 0:
            time.sleep(0.0001)
        while self.ser2.in_waiting > 0:
            self.ser2.read()

    def setup2(self):
        confirmed = False
        while not confirmed:
            self.ser.write(int(1).to_bytes(1,byteorder='big'))
            time.sleep(1)
            print("write1")
            while self.ser.in_waiting > 0:
                print("read1")
                self.ser.read()
                print("confirmed1")
                confirmed = True
        time.sleep(1)

        confirmed = False
        while not confirmed:
            self.ser2.write(int(1).to_bytes(1,byteorder='big'))
            time.sleep(1)
            print("write2")
            while self.ser2.in_waiting > 0:
                print("read2")
                self.ser2.read()
                print("confirmed2")
                confirmed = True
        time.sleep(1)

    def get_screen(self):
        screen = self.screen
        if screen is not None:
            self.screen = None
            self.queue = screen.queue
        return screen

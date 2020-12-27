import time
import colorsys
from threading import Thread

from SerialCommunicator import SerialCommunicator
from AudioVisualRunner import AudioVisualRunner

HSV_H = 23/24

class LEDLights:

    def __init__(self, code_directory, smoothing=0, sample_per=0.04):

        self.serial = SerialCommunicator()
        self.runner = AudioVisualRunner(code_directory, smoothing=smoothing)

        self.curr_color = 0
        self.sample_per = sample_per
        self.colors_delayed = [(0,0,0)] * 27

        self.stop = False
        self.paused = False

    def update(self):

        if self.stop:
            return -1

        if self.paused:
            return 0.25

        if not self.runner.isPlaying():
            delay = 0.5
            self.runner.loadNextSong(delay=delay)
            return delay + self.sample_per

        start_time = time.clock_gettime(time.CLOCK_MONOTONIC)

        midpoint, proportions = self.runner.getAnalysis()
        proportion = proportions[0]**5

        self.curr_color += 0.0003

        color = colorsys.hsv_to_rgb(self.curr_color+midpoint*2/3,1,proportion)
        color_delayed = color

        self.colors_delayed.insert(0, color_delayed)
        orange = self.colors_delayed.pop()

        self.serial.send_color2(color[0], color[1], color[2], orange[0], orange[1], orange[2])

        duration = time.clock_gettime(time.CLOCK_MONOTONIC) - start_time
        return max(self.sample_per - duration, 0)

    def play(self):
        if self.paused:
            self.paused = False
            self.runner.play()

    def pause(self):
        if not self.paused:
            self.paused = True
            self.runner.pause()

    def skip(self):
        self.runner.loadNextSong()

    def terminate(self):
        self.runner.terminate()
        self.stop = True


def main(code_directory="."):

    lights = LEDLights(code_directory, smoothing=0, sample_per=0.04)
    thread = Thread(target=loop, args=(lights,))
    thread.start()
    return lights, thread, lights.serial.get_screen()

def loop(lights):
    delay = 0
    while delay >= 0:
        time.sleep(delay)
        delay = lights.update()

import time
import colorsys
from threading import Thread

from SerialCommunicator import SerialCommunicator
from AudioVisualRunner import AudioVisualRunner

class LEDLights:

    def __init__(self, code_directory, freq_groups, smoothing=0, sample_per=0.04):

        self.serial = SerialCommunicator()
        self.runner = AudioVisualRunner(code_directory, freq_groups, smoothing=smoothing, get_midpoint=True)

        self.colors = [(0,0,0)] * 25
        self.curr_color = 0
        self.sample_per = sample_per

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

        red = []
        green = []
        blue = []

        color = colorsys.hsv_to_rgb(self.curr_color+midpoint*2/3,1,proportion)
        self.colors.insert(0, color)
        self.colors.pop()
        for i in range(len(self.colors)-1, -1, -1):
            red.append(self.colors[i][0])
            green.append(self.colors[i][1])
            blue.append(self.colors[i][2])
        for color in self.colors:
            red.append(color[0])
            green.append(color[1])
            blue.append(color[2])

        self.serial.send_colors(red, green, blue)

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

    freq_meta_groups = [
        {'start':20, 'stop':11000, 'count':1} # all
    ]
    freq_groups = []
    for mg in freq_meta_groups:
        step = (mg['stop'] - mg['start']) / mg['count']
        for i in range(mg['count']):
            freq_groups.append([mg['start']+step*i, mg['start']+step*(i+1)])

    lights = LEDLights(code_directory, freq_groups, smoothing=0, sample_per=0.04)
    thread = Thread(target=loop, args=(lights,))
    thread.start()
    return lights, thread

def loop(lights):
    delay = 0
    while delay >= 0:
        time.sleep(delay)
        delay = lights.update()

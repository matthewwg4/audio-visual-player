import time
import colorsys
from threading import Thread
from os import path
import math

import simpleaudio as sa

from AudioAnalyzer import AudioAnalyzer
from SerialCommunicator import SerialCommunicator

class LEDLights:

    def __init__(self, songs_file, freq_groups, smoothing=0, sample_per=0.04):
        self.serial = SerialCommunicator()

        self.songs_file = songs_file
        self.freq_groups = freq_groups
        self.ranges = 1
        self.min = -100
        self.max = 0
        self.colors = [(0,0,0)] * 25
        self.curr_color = 0
        self.analyzer = None
        self.start_time = 0
        self.last_time = 0
        self.smoothing = smoothing
        self.last_decibels = [-100] * self.ranges
        self.sample_per = sample_per
        self.current_song = None
        self.next_song_info = None
        self.song_setup_process = None

    def setup(self):

        song_path = self.nextSongName()

        self.analyzer = AudioAnalyzer(self.freq_groups, use_cqt=True)
        print("loading song")
        self.analyzer.load(song_path)
        print("song loaded")

        self.serial.setup()

        wave_obj = sa.WaveObject.from_wave_file(song_path)
        self.current_song = wave_obj.play()

        self.start_time = time.clock_gettime(time.CLOCK_MONOTONIC)

        self.song_setup_process = Thread(target=self.loadNextSong)
        self.song_setup_process.start()

        self.last_time = self.start_time + 0.5
        return 0.5 + self.sample_per

    def update(self):

        if not self.current_song.is_playing():

            self.song_setup_process.join()
            self.current_song = self.next_song_info['song'].play()
            self.start_time = time.clock_gettime(time.CLOCK_MONOTONIC)

            self.min = -100
            self.max = 0
            self.analyzer = self.next_song_info['analyzer']
            self.last_decibels = [-100] * self.ranges

            self.song_setup_process = Thread(target=self.loadNextSong)
            self.song_setup_process.start()

            self.last_time = self.start_time + 0.5
            return 0.5 + self.sample_per


        newtime = time.clock_gettime(time.CLOCK_MONOTONIC) + 0.02
        song_time = newtime - self.start_time
        decibels = self.analyzer.get_decibels(self.last_time-self.start_time, song_time)

        self.curr_color += 0.001

        for i in range(self.ranges):
            decibels[i] = (1-self.smoothing)*decibels[i] + self.smoothing*self.last_decibels[i]
        self.last_decibels = decibels

        red = []
        green = []
        blue = []

        db_range = self.max-self.min
        if decibels[0] < self.min + db_range * 0.0002:
            self.min = decibels[0]
        else:
            self.min += db_range * 0.0002 # slight increase
        if decibels[0] > self.max - db_range * 0.0002:
            self.max = decibels[0]
        else:
            self.max -= db_range * 0.0002 # slight decrease
        proportion = (decibels[0]-self.min)/(self.max-self.min)
        #proportion = 1 / (1 + math.exp(-9*(proportion-0.7))) + 0.062
        proportion = proportion**5

        color = colorsys.hsv_to_rgb(self.curr_color,1,proportion)
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
        self.last_time = newtime

        duration = time.clock_gettime(time.CLOCK_MONOTONIC) - newtime + 0.02
        return max(self.sample_per - duration, 0)

    def loadNextSong(self):

        song_path = self.nextSongName()
        analyzer = AudioAnalyzer(self.freq_groups, use_cqt=True)
        analyzer.load(song_path)
        wave_obj = sa.WaveObject.from_wave_file(song_path)

        self.next_song_info = {'analyzer':analyzer, 'song':wave_obj}

    def nextSongName(self):

        song_path = ""
        file_string = ""

        print("Future song selection in progress, do not modify song queue.")

        with open(self.songs_file) as file:
            next_line = file.readline()
            found_song = False
            while next_line and (not found_song):
                if path.exists("songs/{}".format(next_line.strip())):
                    song_path = "songs/{}".format(next_line.strip())
                    found_song = True
                next_line = file.readline()
            while next_line and found_song:
                file_string += "{}\n".format(next_line.strip())
                next_line = file.readline()
            if found_song:
                file_string += song_path[6:]

        with open(self.songs_file, "w") as file:
            file.write(file_string)

        print("Future song selection completed, song queue is safe to modify.")
        print("Next song: {}".format(song_path[6:]))

        return song_path

    # End of LEDLights Class

def main():

    freq_meta_groups = [
        {'start':20, 'stop':11000, 'count':1} # all
    ]
    freq_groups = []
    for mg in freq_meta_groups:
        step = (mg['stop'] - mg['start']) / mg['count']
        for i in range(mg['count']):
            freq_groups.append([mg['start']+step*i, mg['start']+step*(i+1)])

    lights = LEDLights("songs.txt", freq_groups, smoothing=0, sample_per=0.04)
    delay = lights.setup()
    time.sleep(delay)
    while True:
        delay = lights.update()
        time.sleep(delay)

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
        self.ranges = len(freq_groups) + 4
        self.min = -300
        self.max = 0
        self.colors = [i/self.ranges+0.5 for i in range(self.ranges)]
        self.analyzer = None
        self.start_time = 0
        self.last_time = 0
        self.smoothing = smoothing
        self.last_decibels = [-100] * self.ranges
        self.sample_per = sample_per
        self.current_song = None
        self.next_song_info = None
        self.song_setup_process = None

        self.beats = None
        self.next_beat = 0
        self.show_beats = []

        self.ranges -= 4

    def setup(self):

        song_path = self.nextSongName()

        self.analyzer = AudioAnalyzer(self.freq_groups)
        print("loading song")
        self.analyzer.load(song_path)
        print("song loaded")

        self.serial.setup()

        wave_obj = sa.WaveObject.from_wave_file(song_path)
        self.current_song = wave_obj.play()

        self.start_time = time.clock_gettime(time.CLOCK_MONOTONIC)

        self.song_setup_process = Thread(target=self.loadNextSong)
        self.song_setup_process.start()

        self.beats = self.analyzer.get_beats()

        self.last_time = self.start_time + 0.5
        return 0.5 + self.sample_per

    def update(self):

        if not self.current_song.is_playing():

            self.song_setup_process.join()
            self.current_song = self.next_song_info['song'].play()
            self.start_time = time.clock_gettime(time.CLOCK_MONOTONIC)

            self.min = -300
            self.max = 0
            self.analyzer = self.next_song_info['analyzer']
            self.last_decibels = [-100] * self.ranges

            self.beats = self.analyzer.get_beats()
            self.next_beat = 0

            self.song_setup_process = Thread(target=self.loadNextSong)
            self.song_setup_process.start()

            self.last_time = self.start_time + 0.5
            return 0.5 + self.sample_per


        newtime = time.clock_gettime(time.CLOCK_MONOTONIC) + 0.02
        song_time = newtime - self.start_time
        decibels = self.analyzer.get_decibels(self.last_time-self.start_time, song_time)

        if self.next_beat != len(self.beats) and song_time > self.beats[self.next_beat]:
            self.next_beat += 1
            self.show_beats.append(0)
            self.show_beats.append(-1)
        white_squares = []
        while len(self.show_beats) > 0:
            if self.show_beats[0] > 25:
                del self.show_beats[0]
            else:
                break
        for i in range(len(self.show_beats)):
            white_squares.append(25 + self.show_beats[i])
            white_squares.append(24 - self.show_beats[i])
            self.show_beats[i] += 1

        for i in range(self.ranges):
            decibels[i] = (1-self.smoothing)*decibels[i] + self.smoothing*self.last_decibels[i]
        self.last_decibels = decibels

        db_spread = [decibels[0]*3, decibels[0]*2+decibels[1]]
        for i in range(self.ranges - 2):
            db_spread.append(decibels[i]+decibels[i+1]+decibels[i+2])
        db_spread.append(decibels[-2]+decibels[-1]*2)
        db_spread.append(decibels[-1]*3)
        decibels = db_spread
        ranges = len(decibels)

        red = []
        green = []
        blue = []

        for i in range(ranges):
            db_range = self.max-self.min
            if decibels[i] < self.min + db_range * 0.00001:
                self.min = decibels[i]
            else:
                self.min += db_range * 0.00001 # slight increase
            if decibels[i] > self.max - db_range * 0.00001:
                self.max = decibels[i]
            else:
                self.max -= db_range * 0.00001 # slight decrease
            proportion = (decibels[i]-self.min)/(self.max-self.min)
            #proportion = 1 / (1 + math.exp(-9*(proportion-0.7))) + 0.062
            proportion = proportion**5

            saturation = 0 if (i in white_squares) else 1
            color = colorsys.hsv_to_rgb(self.colors[i],saturation,proportion)
            red.append(color[0])
            green.append(color[1])
            blue.append(color[2])

        self.serial.send_colors(red, green, blue)
        self.last_time = newtime

        duration = time.clock_gettime(time.CLOCK_MONOTONIC) - newtime + 0.02
        return max(self.sample_per - duration, 0)

    def loadNextSong(self):

        song_path = self.nextSongName()
        analyzer = AudioAnalyzer(self.freq_groups)
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
        {'start':20, 'stop':60, 'count':5},      # sub-bass
        {'start':60, 'stop':250, 'count':7},     # bass
        {'start':250, 'stop':500, 'count':8},    # low-midrange
        {'start':500, 'stop':2000, 'count':9},   # midrange
        {'start':2000, 'stop':4000, 'count':8},  # upper-midrange
        {'start':4000, 'stop':6000, 'count':6},  # presence
        {'start':6000, 'stop':11000, 'count':5}  # brilliance
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

import time
import colorsys
from threading import Thread
from os import path
import random
import math

from tkinter import Tk, Canvas, Frame, BOTH
import simpleaudio as sa

from AudioAnalyzer import AudioAnalyzer


class AudioVisualizer(Frame):

    def __init__(self, songs_file, freq_groups, smoothing=0, sample_per=40):
        super().__init__()

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
        self.last_decibels = [-40] * self.ranges
        self.sample_per = sample_per
        self.current_song = None
        self.next_song_info = None
        self.song_setup_process = None

        self.ranges -= 4
        self.initUI()

    def initUI(self):

        self.master.title("Audio Visualizer")
        self.pack(fill=BOTH, expand=1)

        canvas = Canvas(self, background="black")
        canvas.pack(fill=BOTH, expand=1)
        self.canvas = canvas

        self.playSong()
        self.song_setup_process = Thread(target=self.loadNextSong)
        self.song_setup_process.start()

        self.last_time = self.start_time + 0.5
        canvas.after(500 + self.sample_per, self.onTimer)

    def updateUI(self):

        self.canvas.delete("all")

        if not self.current_song.is_playing():

            self.song_setup_process.join()
            self.current_song = self.next_song_info['song'].play()
            self.start_time = time.clock_gettime(time.CLOCK_MONOTONIC)

            self.min = -300
            self.max = 0
            self.analyzer = self.next_song_info['analyzer']
            self.last_decibels = [0] * self.ranges

            self.song_setup_process = Thread(target=self.loadNextSong)
            self.song_setup_process.start()

            self.last_time = self.start_time + 0.5
            return 500 + self.sample_per


        newtime = time.clock_gettime(time.CLOCK_MONOTONIC)
        song_time = newtime - self.start_time
        decibels = self.analyzer.get_decibels(self.last_time-self.start_time, song_time)

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
            proportion = 1 / (1 + math.exp(-9*(proportion-0.7))) + 0.062


            startX = 20+i*20
            stopX = 35+i*20
            color = '#'+(''.join(('0'+hex(int(x*255))[2:])[-2:] for x in colorsys.hsv_to_rgb(self.colors[i],1,proportion)))
            self.canvas.create_rectangle(startX, 65, stopX, 80, fill=color)

        self.canvas.pack(fill=BOTH, expand=1)
        self.last_time = newtime

        return self.sample_per

    def onTimer(self):

        skip_time = self.updateUI()
        self.canvas.after(skip_time, self.onTimer)

    def playSong(self):

        song_path = self.nextSongName()

        self.analyzer = AudioAnalyzer(self.freq_groups)
        self.analyzer.load(song_path)

        wave_obj = sa.WaveObject.from_wave_file(song_path)
        self.current_song = wave_obj.play()

        self.start_time = time.clock_gettime(time.CLOCK_MONOTONIC)

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

    # End of AudioVisualizer Class

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

    root = Tk()
    vis = AudioVisualizer("songs.txt", freq_groups, smoothing=0, sample_per=40)
    root.geometry("1100x100")
    root.mainloop()


if __name__ == '__main__':
    main()

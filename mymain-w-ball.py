import time
import colorsys
from threading import Thread
from os import path
import random

from tkinter import Tk, Canvas, Frame, BOTH
import simpleaudio as sa

from AudioAnalyzer import AudioAnalyzer

def solver(delta_time, delta_height, a):

    # a =
    b = (delta_height - a * (delta_time**2)) / delta_time # a*(x**2) + b*x = y
    return b

def get_pos(a, b, time, orig_time, orig_height):
    delta_time = time - orig_time
    y = a * (delta_time**2) + b * delta_time
    return y + orig_height

class Ball(Frame):

    def __init__(self):
        super().__init__()

        self.orig_time = 0
        self.orig_height = random.randint(300, 500)
        self.next_time = random.uniform(0.3, 1.5)
        self.next_height = random.randint(300, 500)
        self.aas = [600, 600, 600, 600, 600, 600]
        self.bs = []
        self.initUI()

    def initUI(self):

        self.master.title("Ball")
        self.pack(fill=BOTH, expand=1)

        canvas = Canvas(self, background="black")
        canvas.pack(fill=BOTH, expand=1)
        self.canvas = canvas

        for i in range(6):
            canvas.create_oval(50*i + 100, self.orig_height - 20, 50*i + 120, self.orig_height, fill="#fff")
        self.orig_time = time.clock_gettime(time.CLOCK_MONOTONIC)
        d_height = self.next_height - self.orig_height
        for a in self.aas:
            self.bs.append(solver(self.next_time, d_height, a))
        self.next_time += self.orig_time

        canvas.after(40, self.onTimer)

    def onTimer(self):

        self.canvas.delete("all")
        curr_time = time.clock_gettime(time.CLOCK_MONOTONIC)

        if curr_time >= self.next_time:
            self.orig_time = self.next_time
            self.orig_height = self.next_height
            self.next_time = random.uniform(0.3, 1.5)
            self.next_height = random.randint(300, 500)

            d_height = self.next_height - self.orig_height
            self.bs = []
            for a in self.aas:
                self.bs.append(solver(self.next_time, d_height, a))
            self.next_time += self.orig_time

        for i in range(6):
            pos = get_pos(self.aas[i], self.bs[i], curr_time, self.orig_time, self.orig_height)
            self.canvas.create_oval(50*i + 100, pos - 20, 50*i + 120, pos, fill="#fff")

        self.canvas.pack(fill=BOTH, expand=1)
        self.canvas.after(40, self.onTimer)



class AudioVisualizer(Frame):

    def __init__(self, songs_file, freq_groups, smoothing=0, sample_per=40):
        super().__init__()

        self.songs_file = songs_file
        self.freq_groups = freq_groups
        self.ranges = len(freq_groups)
        self.min = -100
        self.max = 0
        self.colors = list(map(lambda i: '#'+(''.join((hex(int(x*255))+'0')[2:4] for x in colorsys.hsv_to_rgb(i/self.ranges,1,1))), range(self.ranges)))
        self.analyzer = None
        self.start_time = 0
        self.last_time = 0
        self.smoothing = smoothing
        self.last_decibels = [-40] * self.ranges
        self.sample_per = sample_per
        self.current_song = None
        self.next_song_info = None
        self.song_setup_process = None
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

            for i in range(self.ranges):
                startX = int(55+i*1000/self.ranges)
                stopX = int(45+(i+1)*1000/self.ranges)
                color = self.colors[i]
                self.canvas.create_rectangle(startX, 555, stopX, 600, fill=color)

            self.song_setup_process.join()
            self.current_song = self.next_song_info['song'].play()
            self.start_time = time.clock_gettime(time.CLOCK_MONOTONIC)

            self.min = -100
            self.max = 0
            self.analyzer = self.next_song_info['analyzer']
            self.last_decibels = [0] * self.ranges

            self.song_setup_process = Thread(target=self.loadNextSong)
            self.song_setup_process.start()

            self.last_time = self.start_time + 0.5
            return 500 + self.sample_per


        newtime = time.clock_gettime(time.CLOCK_MONOTONIC)
        decibels = self.analyzer.get_decibels(self.last_time-self.start_time+0.01, newtime-self.start_time+0.01)

        for i in range(self.ranges):
            decibels[i] = (1-self.smoothing)*decibels[i] + self.smoothing*self.last_decibels[i]
            db_range = self.max-self.min
            if decibels[i] < self.min + db_range * 0.0001:
                self.min = decibels[i]
            else:
                self.min += db_range * 0.0001 # slight increase
            if decibels[i] > self.max - db_range * 0.0001:
                self.max = decibels[i]
            else:
                self.max -= db_range * 0.0001 # slight decrease
            proportion = (decibels[i]-self.min)/(self.max-self.min)
            if i == 0:
                print("Min: {}, Max: {}, Val: {}".format(self.min, self.max, decibels[i]))

            startX = int(55+i*1000/self.ranges)
            stopX = int(45+(i+1)*1000/self.ranges)
            color = self.colors[i]
            for j in range(int(proportion*10)+1):
                self.canvas.create_rectangle(startX, 555-j*50, stopX, 600-j*50, fill=color)
            # self.canvas.create_rectangle(int(55+i*1000/self.ranges), 450-proportion*400, int(45+(i+1)*1000/self.ranges), 470, fill=self.colors[i])

        self.canvas.pack(fill=BOTH, expand=1)
        self.last_decibels = decibels
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

def main():

    freq_meta_groups = [
        {'start':20, 'stop':60, 'count':2},      # sub-bass
        {'start':60, 'stop':250, 'count':2},     # bass
        {'start':250, 'stop':500, 'count':2},    # low-midrange
        {'start':500, 'stop':2000, 'count':2},   # midrange
        {'start':2000, 'stop':4000, 'count':2},  # upper-midrange
        {'start':4000, 'stop':6000, 'count':2},  # presence
        {'start':6000, 'stop':11000, 'count':2}  # brilliance
    ]
    freq_groups = []
    for mg in freq_meta_groups:
        step = (mg['stop'] - mg['start']) / mg['count']
        for i in range(mg['count']):
            freq_groups.append([mg['start']+step*i, mg['start']+step*(i+1)])

    root = Tk()
    vis = AudioVisualizer("songs.txt", freq_groups, smoothing=0, sample_per=40)
    root.geometry("1100x630")
    root.mainloop()


if __name__ == '__main__':
    #main()
    root = Tk()
    vis = Ball()
    root.geometry("500x500")
    root.mainloop()

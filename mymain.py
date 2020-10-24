import time
import colorsys
from threading import Thread
from os import path
import random

from tkinter import Tk, Canvas, Frame, BOTH
import simpleaudio as sa

from AudioAnalyzer import AudioAnalyzer

def solver(delta_time, delta_height):
    a = 1500
    b = (delta_height - a * (delta_time**2)) / delta_time # a*(x**2) + b*x = y
    return b

def get_pos(a, b, time, orig_time, orig_height):
    delta_time = time - orig_time
    y = a * (delta_time**2) + b * delta_time
    return y + orig_height


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

        # beat-tracking bouncing ball
        self.beats = None
        self.next_beat = 1
        self.orig_time = 0
        self.orig_height = 755
        self.next_time = 0
        self.next_height = 0
        self.orig_beat_band = self.ranges // 2
        self.next_beat_band = 0
        self.ball_color = self.colors[self.orig_beat_band]
        self.a = 1500
        self.b = 0

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

        # draw ball setup
        self.beats = self.analyzer.get_beats()
        self.next_time = self.beats[0]
        self.next_beat_band, decibel = self.analyzer.get_max_decibels_at_time(self.next_time)
        proportion = min((decibel-self.min)/(self.max-self.min),1.0)
        self.next_height = 755 - (int(proportion*10))*50
        self.b = solver(self.next_time, self.next_height - self.orig_height)

        self.last_time = self.start_time + 0.5
        canvas.after(500 + self.sample_per, self.onTimer)

    def updateUI(self):

        self.canvas.delete("all")

        if not self.current_song.is_playing():

            for i in range(self.ranges):
                startX = int(55+i*1000/self.ranges)
                stopX = int(45+(i+1)*1000/self.ranges)
                color = self.colors[i]
                self.canvas.create_rectangle(startX, 755, stopX, 800, fill=color)

            self.song_setup_process.join()
            self.current_song = self.next_song_info['song'].play()
            self.start_time = time.clock_gettime(time.CLOCK_MONOTONIC)

            self.min = -100
            self.max = 0
            self.analyzer = self.next_song_info['analyzer']
            self.last_decibels = [0] * self.ranges

            self.song_setup_process = Thread(target=self.loadNextSong)
            self.song_setup_process.start()

            # draw ball setup
            self.beats = self.analyzer.get_beats()
            self.next_time = self.beats[0]
            self.next_beat = 1
            self.next_beat_band, decibel = self.analyzer.get_max_decibels_at_time(self.next_time)
            proportion = min((decibel-self.min)/(self.max-self.min),1.0)
            self.next_height = 755 - (int(proportion*10))*50
            self.orig_height = 755
            self.b = solver(self.next_time, self.next_height - self.orig_height)
            self.canvas.create_oval(1070, self.orig_height - 20, 1090, self.orig_height, fill="#ffffff")#self.ball_color)

            self.last_time = self.start_time + 0.5
            return 500 + self.sample_per


        newtime = time.clock_gettime(time.CLOCK_MONOTONIC)
        song_time = newtime - self.start_time
        decibels = self.analyzer.get_decibels(self.last_time-self.start_time, song_time)

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

            startX = int(55+i*1000/self.ranges)
            stopX = int(45+(i+1)*1000/self.ranges)
            color = self.colors[i]
            for j in range(int(proportion*10)+1):
                self.canvas.create_rectangle(startX, 755-j*50, stopX, 800-j*50, fill=color)

        # draw ball
        if song_time >= self.next_time:
            self.orig_time = self.next_time
            self.orig_beat_band = self.next_beat_band
            self.ball_color = self.colors[self.orig_beat_band]
            self.next_beat += 1
            if self.next_beat < self.beats.shape[0]:
                self.next_time = self.beats[self.next_beat]
                self.next_beat_band, decibel = self.analyzer.get_max_decibels_at_time(self.next_time)
                proportion = min((decibel-self.min)/(self.max-self.min),1.0)
                self.orig_height = self.next_height
                self.next_height = 755 - (int(proportion*10))*50
                self.b = solver(self.next_time - self.orig_time, self.next_height - self.orig_height)

                startX = int(55+self.orig_beat_band*1000/self.ranges)
                stopX = int(45+(self.orig_beat_band+1)*1000/self.ranges)
                color = self.colors[self.orig_beat_band]
                self.canvas.create_rectangle(startX, 255, stopX, 800, fill="#000000")
                for j in range((805-self.orig_height)//50):
                    self.canvas.create_rectangle(startX, 755-j*50, stopX, 800-j*50, fill=color)
                    #self.canvas.create_rectangle(startX, self.orig_height, stopX, self.orig_height+45, fill=color)
            else:
                self.orig_time = song_time
                self.next_time = song_time + 1.0
                self.orig_height = 755 - (755 - self.orig_height)*0.98
        pos = get_pos(self.a, self.b, song_time, self.orig_time, self.orig_height)
        time_proportion = (song_time - self.orig_time)/(self.next_time - self.orig_time)
        h_pos_band = (1 - time_proportion)*self.orig_beat_band + time_proportion*self.next_beat_band
        h_pos = int((55+h_pos_band*1000/self.ranges) + (500/self.ranges+5))
        for i in range(self.ranges):
            startX = int(55+i*1000/self.ranges)
            stopX = int(45+(i+1)*1000/self.ranges)
            if (startX <= h_pos and stopX >= h_pos) or (startX <= h_pos - 20 and stopX >= h_pos - 20):
                self.canvas.create_rectangle(startX, 255, stopX, 800-((800-pos)//50)*50, fill="#000000")
        self.canvas.create_oval(h_pos - 20, pos - 20, h_pos, pos, fill="#ffffff")#self.ball_color)

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

    # End of AudioVisualizer Class

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
    root.geometry("1100x830")
    root.mainloop()


if __name__ == '__main__':
    main()

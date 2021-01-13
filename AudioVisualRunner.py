import time
import os
from threading import Lock

import vlc

from AudioAnalyzer import AudioAnalyzer

class AudioVisualRunner:

    def __init__(self, code_directory, songs_file="songs.txt", queue_file="queue.txt", smoothing=0, db_range_reduce=None, get_midpoint=False):

        self.songs_file = os.path.join(code_directory, songs_file)
        self.queue_file = os.path.join(code_directory, queue_file)
        self.songs_folder = os.path.join(code_directory, "songs")
        self.data_folder = os.path.join(code_directory, "songs-data")
        self.min = -100
        self.max = 0
        self.db_range_reduce = db_range_reduce if db_range_reduce != None else 0.0002
        self.analyzer = None
        self.smoothing = smoothing
        self.last_decibels = [-100]
        self.current_song = None
        self.start_time = 0
        self.last_time = 0
        self.get_midpoint = get_midpoint
        self.lock = Lock()
        self.pause_time = None

    def isPlaying(self):
        return self.current_song != None and self.current_song.is_playing()

    def loadNextSong(self, delay=0.5):

        self.lock.acquire()

        if self.isPlaying():
            self.current_song.stop()
        song_path, data_path = self.nextSongName()

        self.analyzer = AudioAnalyzer()
        self.analyzer.load(data_path)

        self.min = -100
        self.max = 0
        self.last_decibels = [-100]

        self.current_song = vlc.MediaPlayer(song_path)
        self.current_song.play()
        while not self.current_song.is_playing():
            time.sleep(0.001)
        self.start_time = time.clock_gettime(time.CLOCK_MONOTONIC)
        self.last_time = self.start_time + delay

        self.lock.release()

    def getAnalysis(self):

        self.lock.acquire()

        newtime = time.clock_gettime(time.CLOCK_MONOTONIC) + 0.02
        total_time = self.last_time - self.start_time
        song_time = newtime - self.start_time
        decibels = midpoint = None
        self.last_time = newtime

        if self.get_midpoint:
            midpoint, db = self.analyzer.get_midpoint(total_time, song_time)
            decibels = [db]
        else:
            decibels = self.analyzer.get_decibels(total_time, song_time)
        proportions = []

        for i in range(1):
            decibels[i] = (1-self.smoothing)*decibels[i] + self.smoothing*self.last_decibels[i]
            db_range = self.max-self.min
            if decibels[i] < self.min + db_range * self.db_range_reduce:
                self.min = decibels[i]
            else:
                self.min += db_range * self.db_range_reduce # slight increase
            if decibels[i] > self.max - db_range * self.db_range_reduce:
                self.max = decibels[i]
            else:
                self.max -= db_range * self.db_range_reduce # slight decrease
            proportions.append((decibels[i]-self.min)/(self.max-self.min))
        self.last_decibels = decibels

        self.lock.release()

        if self.get_midpoint:
            return midpoint, proportions
        else:
            return proportions

    def nextSongName(self):

        song_path = ""
        data_path = ""
        song_name = ""
        file_string = ""

        with open(self.queue_file) as file:
            next_line = file.readline()
            found_song = False
            while next_line and (not found_song):
                pos_song_path = os.path.join(self.songs_folder, next_line.strip() + ".mp3")
                pos_data_path = os.path.join(self.data_folder, next_line.strip())
                if os.path.exists(pos_song_path) and os.path.exists(pos_data_path):
                    song_path = pos_song_path
                    data_path = pos_data_path
                    song_name = next_line.strip()
                    found_song = True
                else:
                    if not os.path.exists(pos_song_path):
                        print("Song not found: {}".format(pos_song_path))
                    if not os.path.exists(pos_data_path):
                        print("Data not found: {}".format(pos_data_path))
                next_line = file.readline()
            while next_line and found_song:
                file_string += "{}\n".format(next_line.strip())
                next_line = file.readline()

        with open(self.queue_file, "w") as file:
            file.write(file_string)

        if found_song:
            print("Next song: {}".format(song_name))
            return song_path, data_path

        file_string = ""
        with open(self.songs_file) as file:
            next_line = file.readline()
            found_song = False
            while next_line and (not found_song):
                pos_song_path = os.path.join(self.songs_folder, next_line.strip() + ".mp3")
                pos_data_path = os.path.join(self.data_folder, next_line.strip())
                if os.path.exists(pos_song_path) and os.path.exists(pos_data_path):
                    song_path = pos_song_path
                    data_path = pos_data_path
                    song_name = next_line.strip()
                    found_song = True
                else:
                    if not os.path.exists(pos_song_path):
                        print("Song not found: {}".format(pos_song_path))
                    if not os.path.exists(pos_data_path):
                        print("Data not found: {}".format(pos_data_path))
                next_line = file.readline()
            while next_line and found_song:
                file_string += "{}\n".format(next_line.strip())
                next_line = file.readline()
            if found_song:
                file_string += song_name

        with open(self.songs_file, "w") as file:
            file.write(file_string)

        print("Next song: {}".format(song_name))

        return song_path, data_path

    def play(self):
        self.lock.acquire()
        if self.pause_time != None:
            self.current_song.play()
            curr_time = time.clock_gettime(time.CLOCK_MONOTONIC)
            self.start_time += curr_time - self.pause_time
            self.pause_time = None
        self.lock.release()

    def pause(self):
        self.lock.acquire()
        if self.isPlaying() and self.pause_time == None:
            self.current_song.pause()
            self.pause_time = time.clock_gettime(time.CLOCK_MONOTONIC)
        self.lock.release()

    def terminate(self):
        self.lock.acquire()
        if self.isPlaying():
            self.current_song.stop()
        self.lock.release()
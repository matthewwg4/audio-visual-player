from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext
import os
import sys
from threading import Thread
import time


import run_leds
from download_playlist import download_playlist
import playlist

class App:

    def __init__(self,  code_directory=".", playlist_folder="playlists", songs_folder="songs",
            data_folder="songs-data", song_file="songs.txt", queue_file="queue.txt"):
        self.code_directory = code_directory
        self.playlist_folder = playlist_folder
        self.playlist_directory = os.path.join(code_directory, playlist_folder)
        self.songs_directory = os.path.join(code_directory, songs_folder)
        self.data_directory = os.path.join(code_directory, data_folder)
        self.song_file = os.path.join(code_directory, song_file)
        self.queue_file = os.path.join(code_directory, queue_file)
        self.window = None
        self.link = None
        self.playlist = None
        self.runner = self.running_thread = None
        self.downloaders = []
        self.queue_thread = None
        self.queue_check_time = 0.25
        self.queue = [[],[]]
        self.playlist_songs = self.all_songs = None

    def main(self):

        window = Tk()
        window.title("AudioVisualizer App")
        self.window = window

        tab_control = ttk.Notebook(window)
        tab1 = ttk.Frame(tab_control)
        tab2 = ttk.Frame(tab_control)
        tab_control.add(tab1, text='Play Music')
        tab_control.add(tab2, text='Download Music')

        lbl1 = Label(tab1, text= 'Play From Playlist:')
        lbl1.grid(column=0, row=0)
        self.playlist = ttk.Combobox(tab1, state="readonly")
        self.playlist['values'] = tuple([x[:-4] for x in os.listdir(os.path.join(self.code_directory, self.playlist_folder)) if len(x) > 4 and x[-4:] == '.txt'])
        self.playlist.current(0)
        self.playlist.grid(column=1, row=0)
        btn1 = Button(tab1, text="Play Music", command=self.clicked1)
        btn1.grid(column=2, row=0)
        play_btn = Button(tab1, text="Play Song", command=self.play)
        play_btn.grid(column=0, row=1)
        pause_btn = Button(tab1, text="Pause Song", command=self.pause)
        pause_btn.grid(column=1, row=1)
        nxt = Button(tab1, text="Next Song", command=self.skip)
        nxt.grid(column=2, row=1)
        self.queue_txt = scrolledtext.ScrolledText(tab1, width=60, height=15, pady=5)
        self.queue_txt.grid(column=0, row=2, columnspan=3)
        lbl1a = Label(tab1, text= 'Add to Queue From Playlist:')
        lbl1a.grid(column=0, row=3, columnspan=3)
        self.playlist_songs = ttk.Combobox(tab1, state="readonly", width=40)
        self.playlist_songs.grid(column=0, row=4, columnspan=2)
        btn1a = Button(tab1, text="Add to Queue", command=self.queue_add_playlist)
        btn1a.grid(column=2, row=4)
        lbl1b = Label(tab1, text= 'Add to Queue From All Songs:')
        lbl1b.grid(column=0, row=5, columnspan=3)
        self.all_songs = ttk.Combobox(tab1, state="readonly", width=40)
        self.all_songs['values'] = self.read_songs()
        self.all_songs.current(0)
        self.all_songs.grid(column=0, row=6, columnspan=2)
        btn1b = Button(tab1, text="Add to Queue", command=self.queue_add_all)
        btn1b.grid(column=2, row=6)
        lbl1c = Label(tab1, text= 'Remove From Upcoming Songs:')
        lbl1c.grid(column=0, row=7, columnspan=3)
        self.remove_songs = ttk.Combobox(tab1, state="readonly", width=40)
        self.remove_songs.grid(column=0, row=8, columnspan=2)
        btn1c = Button(tab1, text="Remove Song", command=self.queue_remove)
        btn1c.grid(column=2, row=8)

        lbl2 = Label(tab2, text= 'Spotify Playlist Link:')
        lbl2.grid(column=0, row=0)
        self.link = Entry(tab2, width=20)
        self.link.grid(column=1, row=0)
        btn2 = Button(tab2, text="Download Playlist", command=self.clicked2)
        btn2.grid(column=2, row=0)

        tab_control.pack(expand=1, fill='both')
        window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.queue_thread = Thread(target=self.queue_check,)
        self.queue_thread.start()
        window.mainloop()

    def read_songs(self, playlist="all.txt"):
        songs = []
        with open(os.path.join(self.playlist_directory, playlist)) as file:
            next_line = file.readline()
            while next_line:
                song_name = next_line.strip()
                pos_song_path = os.path.join(self.songs_directory, song_name + ".mp3")
                pos_data_path = os.path.join(self.data_directory, song_name)
                if os.path.exists(pos_song_path) and os.path.exists(pos_data_path):
                    songs.append(song_name)
                next_line = file.readline()
        return tuple(songs)

    def clicked1(self):
        playlist.set_playlist(self.code_directory, self.playlist_folder, self.playlist.get() + '.txt', True)
        if self.runner == None:
            self.runner, self.running_thread = run_leds.main(self.code_directory, 'default')
        else:
            self.runner.skip()
        self.playlist_songs['values'] = self.read_songs(self.playlist.get() + '.txt')
        self.playlist_songs.current(0)


    def clicked2(self):
        self.downloaders.append(download_playlist(self.link.get()))

    def play(self):
        if self.runner != None:
            self.runner.play()

    def pause(self):
        if self.runner != None:
            self.runner.pause()

    def skip(self):
        if self.runner != None:
            self.runner.skip()

    def on_closing(self):
        if self.runner != None:
            self.runner.terminate()
            self.running_thread.join()
        self.queue_check_time = -1
        self.queue_thread.join()
        with open(self.queue_file, 'w') as file:
            file.write("")
        print("Waiting for download(s) to finish")
        for downloader in self.downloaders:
            downloader.join()
        print("Shutting down")
        self.window.destroy()

    # queue handling functions:

    def queue_check(self):

        while self.queue_check_time >= 0:
            time.sleep(self.queue_check_time)
            if self.runner == None:
                continue
            # get queue
            curr_queue = []
            count = 0
            with open(self.queue_file) as file:
                qq = []
                next_line = file.readline()
                while next_line and count < 9:
                    song_name = next_line.strip()
                    pos_song_path = os.path.join(self.songs_directory, song_name + ".mp3")
                    pos_data_path = os.path.join(self.data_directory, song_name)
                    if os.path.exists(pos_song_path) and os.path.exists(pos_data_path):
                        qq.append(song_name)
                        count += 1
                    next_line = file.readline()
                curr_queue.append(qq)
            with open(self.song_file) as file:
                sq = []
                next_line = file.readline()
                while next_line and count < 9:
                    song_name = next_line.strip()
                    pos_song_path = os.path.join(self.songs_directory, song_name + ".mp3")
                    pos_data_path = os.path.join(self.data_directory, song_name)
                    if os.path.exists(pos_song_path) and os.path.exists(pos_data_path):
                        sq.append(song_name)
                        count += 1
                    next_line = file.readline()
                curr_queue.append(sq)
            # check queue
            if len(curr_queue[0]) != len(self.queue[0]) or len(curr_queue[1]) != len(self.queue[1]):
                self.queue = curr_queue
                self.queue_update()
                continue
            correct_queue = True
            for i in range(2):
                for j in range(len(curr_queue[i])):
                    correct_queue = correct_queue and (curr_queue[i][j] == self.queue[i][j])
            if not correct_queue:
                self.queue = curr_queue
                self.queue_update()

    def queue_update(self):

        queue_string = "--- Upcoming Songs ---\n"
        if len(self.queue[0]) > 0:
            queue_string += "~~~~ From Queue ~~~~\n"
        for str in self.queue[0]:
            queue_string += "> " + str + "\n"
        if len(self.queue[1]) > 0:
            queue_string += "~~~~ From Playlist ~~~~\n"
        for str in self.queue[1]:
            queue_string += "> " + str + "\n"
        self.queue_txt.delete('1.0', END)
        self.queue_txt.insert(INSERT, queue_string)

        q = self.queue[0] + self.queue[1]
        for i in range(len(q)):
            same = []
            for j in range(i+1, len(q)):
                if q[i] == q[j]:
                    same.append(j)
            if len(same) > 0:
                q[i] += "  (1)"
                for j in range(len(same)):
                    q[same[j]] += "  ({})".format(j+2)
        self.remove_songs['values'] = tuple(q)
        self.remove_songs.current(0)

    def queue_add_playlist(self):
        song = self.playlist_songs.get()
        self.queue_add(song)

    def queue_add_all(self):
        song = self.all_songs.get()
        self.queue_add(song)

    def queue_add(self, song):
        with open(self.queue_file, 'a') as file:
            file.write(song + '\n')

    def queue_remove(self):
        indx = self.remove_songs.current()
        filename = self.queue_file if indx < len(self.queue[0]) else self.song_file

        songs = []
        with open(filename, 'r') as file:
            next_line = file.readline()
            while next_line:
                songs.append(next_line.strip())
                next_line = file.readline()

        if indx < len(self.queue[0]):
            songs.pop(indx)
        else:
            removed = songs.pop(indx - len(self.queue[0]))
            songs.append(removed)

        str = '\n'.join(songs)
        with open(filename, 'w') as file:
            file.write(str)

if __name__ == '__main__':
    directory = sys.argv[1]
    app = App(code_directory=directory)
    app.main()

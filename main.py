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
        self.new_playlist_name = None
        self.link = None
        self.playlist = None
        self.runner = self.running_thread = self.screen = None
        self.downloaders = []
        self.queue_thread = None
        self.queue_check_time = 0.25
        self.queue = [[],[]]
        self.playlist_songs = self.all_songs = None
        self.slated_changes = []

    def main(self):

        window = Tk()
        window.title("AudioVisualizer App")
        self.window = window

        tab_control = ttk.Notebook(window)
        tab1 = ttk.Frame(tab_control)
        tab2 = ttk.Frame(tab_control)
        tab3 = ttk.Frame(tab_control)
        tab_control.add(tab1, text='Play Music')
        tab_control.add(tab2, text='Download Music')
        tab_control.add(tab3, text='Manage Music (Not Functional)')

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
        self.queue_txt = scrolledtext.ScrolledText(tab1, width=69, height=15, pady=5)
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
        #self.all_songs.current(0)
        self.all_songs.grid(column=0, row=6, columnspan=2)
        btn1b = Button(tab1, text="Add to Queue", command=self.queue_add_all)
        btn1b.grid(column=2, row=6)
        lbl1c = Label(tab1, text= 'Remove From Upcoming Songs:')
        lbl1c.grid(column=0, row=7, columnspan=3)
        self.remove_songs = ttk.Combobox(tab1, state="readonly", width=40)
        self.remove_songs.grid(column=0, row=8, columnspan=2)
        btn1c = Button(tab1, text="Remove Song", command=self.queue_remove)
        btn1c.grid(column=2, row=8)

        self.radio_val = IntVar()
        self.radio_val.set(1)
        r1 = Radiobutton(tab2, text="Create new playlist", variable=self.radio_val, value=1, command=self.show_textbox)
        r2 = Radiobutton(tab2, text="Append to existing playlist", variable=self.radio_val, value=2, command=self.show_list)
        r1.grid(column=0, row=0)
        r2.grid(column=1, row=0, columnspan=2)
        self.name_label = Label(tab2, text= 'New Playlist Name:')
        self.name_label.grid(column=0, row=1)
        self.new_playlist_name = Entry(tab2, width=20)
        self.new_playlist_name.grid(column=1, row=1)
        self.add_to = Label(tab2, text= 'Add to Playlist:')
        self.append_playlist = ttk.Combobox(tab2, state="readonly")
        self.append_playlist['values'] = tuple([x[:-4] for x in os.listdir(os.path.join(self.code_directory, self.playlist_folder)) if len(x) > 4 and x[-4:] == '.txt' and x != 'all.txt'])
        lbl2 = Label(tab2, text= 'YouTube (Music) Playlist Link:')
        lbl2.grid(column=0, row=2)
        self.link = Entry(tab2, width=20)
        self.link.grid(column=1, row=2)
        btn2 = Button(tab2, text="Download Playlist", command=self.clicked2)
        btn2.grid(column=2, row=2)


        lib_manage_lbl = Label(tab3, text= '-------- Manage Library --------')
        lib_manage_lbl.grid(column=0, row=0, columnspan=3, pady=5)
        lib_song_lbl = Label(tab3, text= 'For song:')
        lib_song_lbl.grid(column=0, row=1)
        self.lib_song = ttk.Combobox(tab3, state="readonly", width=32)
        self.lib_song['values'] = self.read_songs()
        self.lib_song.grid(column=1, row=1)
        lib_song_rn_lbl = Label(tab3, text= 'Rename to:')
        lib_song_rn_lbl.grid(column=0, row=2)
        self.lib_song_rn = Entry(tab3, width=32)
        self.lib_song_rn.grid(column=1, row=2)
        lib_song_rn_btn = Button(tab3, text="Rename Song", command=self.rename_song)
        lib_song_rn_btn.grid(column=2, row=2)
        lib_song_dlt_lbl = Label(tab3, text= 'Delete song:')
        lib_song_dlt_lbl.grid(column=0, row=3)
        lib_song_dlt_btn = Button(tab3, text="Delete Song", command=self.delete_song)
        lib_song_dlt_btn.grid(column=1, row=3)

        pl_manage_lbl = Label(tab3, text= '-------- Manage Playlists --------')
        pl_manage_lbl.grid(column=0, row=4, columnspan=3, pady=5)
        pl_pl_lbl = Label(tab3, text= 'For playlist:')
        pl_pl_lbl.grid(column=0, row=5)
        self.pl_pl = ttk.Combobox(tab3, state="readonly", width=32)
        self.pl_pl['values'] = tuple([x[:-4] for x in os.listdir(os.path.join(self.code_directory, self.playlist_folder)) if len(x) > 4 and x[-4:] == '.txt' and x != 'all.txt'])
        self.pl_pl.grid(column=1, row=5)
        self.pl_pl.bind("<<ComboboxSelected>>", self.pl_sel_update)
        pl_pl_rn_lbl = Label(tab3, text= 'Rename to:')
        pl_pl_rn_lbl.grid(column=0, row=6)
        self.pl_pl_rn = Entry(tab3, width=32)
        self.pl_pl_rn.grid(column=1, row=6)
        pl_pl_rn_btn = Button(tab3, text="Rename Playlist", command=self.rename_playlist)
        pl_pl_rn_btn.grid(column=2, row=6)
        pl_pl_dlt_lbl = Label(tab3, text= 'Delete Playlist:')
        pl_pl_dlt_lbl.grid(column=0, row=7)
        pl_pl_dlt_btn = Button(tab3, text="Delete Playlist", command=self.delete_playlist)
        pl_pl_dlt_btn.grid(column=1, row=7)
        pl_merge_lbl = Label(tab3, text= 'Merge into:')
        pl_merge_lbl.grid(column=0, row=8)
        self.pl_merge = ttk.Combobox(tab3, state="readonly", width=32)
        self.pl_merge['values'] = tuple([x[:-4] for x in os.listdir(os.path.join(self.code_directory, self.playlist_folder)) if len(x) > 4 and x[-4:] == '.txt' and x != 'all.txt'])
        self.pl_merge.grid(column=1, row=8)
        pl_merge_btn = Button(tab3, text="Merge Playlists", command=self.merge_playlists)
        pl_merge_btn.grid(column=2, row=8)
        pl_add_song_lbl = Label(tab3, text= 'Add song:')
        pl_add_song_lbl.grid(column=0, row=9)
        self.pl_add_song = ttk.Combobox(tab3, state="readonly", width=32)
        self.pl_add_song['values'] = self.read_songs()
        self.pl_add_song.grid(column=1, row=9)
        pl_add_song_btn = Button(tab3, text="Add Song", command=self.add_song)
        pl_add_song_btn.grid(column=2, row=9)
        pl_rm_song_lbl = Label(tab3, text= 'Remove song:')
        pl_rm_song_lbl.grid(column=0, row=10)
        self.pl_rm_song = ttk.Combobox(tab3, state="readonly", width=32)
        self.pl_rm_song['values'] = self.read_songs()
        self.pl_rm_song.grid(column=1, row=10)
        pl_rm_song_btn = Button(tab3, text="Remove Song", command=self.remove_song)
        pl_rm_song_btn.grid(column=2, row=10)
        pl_create_lbl = Label(tab3, text= 'New Playlist:')
        pl_create_lbl.grid(column=0, row=11)
        self.pl_create = Entry(tab3, width=32)
        self.pl_create.grid(column=1, row=11)
        pl_create_btn = Button(tab3, text="Create Playlist", command=self.create_playlist)
        pl_create_btn.grid(column=2, row=11)
        pl_changes_lbl = Label(tab3, text= 'Slated Changes:')
        pl_changes_lbl.grid(column=0, row=12)
        self.pl_changes = scrolledtext.ScrolledText(tab3, width=50, height=5)
        self.pl_changes.grid(column=1, row=12, columnspan=2, pady=5)
        undo_btn = Button(tab3, text="Undo", command=self.undo)
        undo_btn.grid(column=0, row=13)
        perform_btn = Button(tab3, text="Perform Changes (Occurs Automatically on App Exit)", command=self.perform_changes)
        perform_btn.grid(column=1, row=13, columnspan=2)

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
            self.runner, self.running_thread, self.screen = run_leds.main(self.code_directory, 'default')
            if self.screen is not None:
                self.screen.screen_start()
        else:
            self.runner.skip()
        self.playlist_songs['values'] = self.read_songs(self.playlist.get() + '.txt')
        self.playlist_songs.current(0)


    def clicked2(self):
        if self.radio_val.get() == 1:
            self.downloaders.append(download_playlist(self.code_directory, self.link.get(), self.new_playlist_name.get(), False))
        else:
            self.downloaders.append(download_playlist(self.code_directory, self.link.get(), self.append_playlist.get(), True))

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
        if self.screen != None:
            self.screen.destroy()
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

    # hiding and showing download options

    def show_textbox(self):
        self.name_label.grid(column=0, row=1)
        self.new_playlist_name.grid(column=1, row=1)
        self.add_to.grid_forget()
        self.append_playlist.grid_forget()

    def show_list(self):
        self.add_to.grid(column=0, row=1)
        self.append_playlist.grid(column=1, row=1)
        self.append_playlist.current(0)
        self.name_label.grid_forget()
        self.new_playlist_name.grid_forget()

    # Music management

    def rename_song(self):
        self.slated_changes.append(("Rename song {} to {}".format(self.lib_song.get(), self.lib_song_rn.get()), "SONG", "RENAME", self.lib_song.get(), self.lib_song_rn.get()))
        self.update_changes()

    def delete_song(self):
        self.slated_changes.append(("Delete song {}".format(self.lib_song.get()), "SONG", "DELETE", self.lib_song.get()))
        self.update_changes()

    def rename_playlist(self):
        self.slated_changes.append(("Rename playlist {} to {}".format(self.pl_pl.get(), self.pl_pl_rn.get()), "PLAYLIST", "RENAME", self.pl_pl.get(), self.pl_pl_rn.get()))
        self.update_changes()

    def delete_playlist(self):
        self.slated_changes.append(("Delete playlist {}".format(self.pl_pl.get()), "PLAYLIST", "DELETE", self.pl_pl.get()))
        self.update_changes()

    def merge_playlists(self):
        self.slated_changes.append(("Merge playlist {} into {}".format(self.pl_pl.get(), self.pl_merge.get()), "PLAYLIST", "MERGE", self.pl_pl.get(), self.pl_merge.get()))
        self.update_changes()

    def add_song(self):
        self.slated_changes.append(("Add song {} to playlist {}".format(self.pl_add_song.get(), self.pl_pl.get()), "PLAYLIST", "ADD", self.pl_pl.get(), self.pl_add_song.get()))
        self.update_changes()

    def remove_song(self):
        self.slated_changes.append(("Remove song {} from playlist {}".format(self.pl_rm_song.get(), self.pl_pl.get()), "PLAYLIST", "REMOVE", self.pl_pl.get(), self.pl_rm_song.get()))
        self.update_changes()

    def create_playlist(self):
        self.slated_changes.append(("Create new playlist {}".format(self.pl_create.get()), "PLAYLIST", "CREATE", self.pl_create.get()))
        self.update_changes()

    def undo(self):
        if len(self.slated_changes) > 0:
            self.slated_changes.pop()
            self.update_changes()

    def perform_changes(self):
        self.slated_changes = []
        self.update_changes()

    def update_changes(self):
        update_string = "\n".join([x[0] for x in self.slated_changes])
        self.pl_changes.delete('1.0', END)
        self.pl_changes.insert(INSERT, update_string)

    def pl_sel_update(self, event):
        self.pl_rm_song['values'] = self.read_songs(self.pl_pl.get() + ".txt")

if __name__ == '__main__':
    directory = sys.argv[1]
    app = App(code_directory=directory)
    app.main()

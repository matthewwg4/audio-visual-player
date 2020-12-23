import sys
import os
import signal
import subprocess
from multiprocessing import Process
import time

import convert
import order_playlists

def download_playlist(dir, link, list_name):
    proc = Process(target=download_playlist_from_link, args=(dir, link, list_name))
    proc.start()
    return proc

def download_playlist_from_link(dir, link, list_name, kill_proc=True):
    if list_name is None:
        list_name = "playlist"
    if list_name == "":
        list_name = "playlist"

    pid = os.getpid()
    if kill_proc:
        os.setpgid(pid, pid)

    dir_base = dir
    folder = 'mp3-songs'
    directory = '{}/{}'.format(dir_base, folder)
    exists = os.path.exists(directory)
    i = -1
    while exists:
        i += 1
        exists = os.path.exists(directory + str(i))
    if i >= 0:
        folder += str(i)
        directory += str(i)

    os.mkdir(directory)

    hastracking = True
    song_count = 0
    same_count = 0
    for _ in range(5):

        if not hastracking or song_count == -1:
            break

        try:
            subprocess.run(['spotdl', link], cwd=directory, timeout=300)
        except subprocess.SubprocessError:
            print("Timeout playlist")
        hastracking = False
        trackingfile = ""
        for filename in os.listdir(directory):
            if filename.endswith(".spotdlTrackingFile"):
                hastracking = True
                trackingfile = filename
        if not hastracking:
            break

        new_song_count = len(os.listdir(directory))
        if song_count == new_song_count:
            same_count += 1
            if same_count == 4:
                break
        else:
            same_count = 0
            song_count = new_song_count

        for _ in range(10):
            start_time = time.clock_gettime(time.CLOCK_MONOTONIC)
            try:
                subprocess.run(['spotdl', trackingfile], cwd=directory, timeout=60)
            except subprocess.SubprocessError:
                print("Timeout trackingfile")
            duration = time.clock_gettime(time.CLOCK_MONOTONIC) - start_time
            if duration < 5:
                break
            hastracking = False
            for filename in os.listdir(directory):
                if filename.endswith(".spotdlTrackingFile"):
                    hastracking = True
            if not hastracking:
                break

            new_song_count = len(os.listdir(directory))
            if song_count == new_song_count:
                same_count += 1
                if same_count == 4:
                    song_count = -1
                    break
            else:
                same_count = 0
                song_count = new_song_count

    files = os.listdir(directory)
    mp3_count = 0
    mp4_count = 0
    for filename in files:
        if filename.endswith(".mp3") or filename.endswith(".spotdlTrackingFile"):
            os.remove('{}/{}'.format(directory, filename))
            mp3_count += 1

    for mp4 in os.listdir(os.path.join(directory,"Temp")):
        if mp4.endswith(".mp4"):
            subprocess.run(['ffmpeg', '-i', os.path.join("Temp",mp4), mp4[:-3] + "mp3"], cwd=directory)
            os.remove(os.path.join(directory,"Temp",mp4))
            mp4_count += 1
            print("{}/{} Songs Converted to MP3".format(mp4_count, mp3_count))

    os.rmdir(os.path.join(directory,"Temp"))

    convert.convert_songs_to_data(directory_base=dir_base, mp3_folder=folder, playlist_name=list_name)

    os.rmdir(directory)

    order_playlists.main(dir)
    print("Playlist download complete")

    if kill_proc:
        os.killpg(pid, signal.SIGKILL)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Missing directory or link to playlist")
        exit(-1)
    list_name = "playlist"
    if len(sys.argv) > 3:
        list_name = sys.argv[3]

    download_playlist_from_link(sys.argv[1], sys.argv[2], list_name)

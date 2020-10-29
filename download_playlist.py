import sys
import os
import subprocess
from threading import Thread

import convert
import order_playlists

def download_playlist(link):
    thread = Thread(target=download_playlist_from_link, args=(link,))
    thread.start()
    return thread

def download_playlist_from_link(link):

    dir_base = '/Users/matthewgoldsmith/Documents/python/music-visualizer'
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
    subprocess.run(['spotdl', '-p', link], cwd=directory)

    song_list = os.listdir(directory)[0]
    subprocess.run(['spotdl', '-l', song_list, '--overwrite', 'force'], cwd=directory)

    convert.convert_songs_to_data(directory_base=dir_base, mp3_folder=folder)

    os.remove('{}/{}'.format(directory, song_list))
    os.rmdir(directory)

    order_playlists.main()
    print("Playlist download complete")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Missing link to playlist")
        exit(-1)
    download_playlist_from_link(sys.argv[1])

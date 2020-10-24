import sys
import os
import random

def set_playlist(directory, folder='playlists', filename="all.txt", shuffle=True):
    playlist_path = os.path.join(folder, filename)
    songs = []

    with open(os.path.join(directory, playlist_path), "r") as file:
        next_line = file.readline()
        while next_line:
            songs.append(next_line.strip())
            next_line = file.readline()

    if shuffle:
        random.shuffle(songs)
    playlist = "\n".join(songs)

    with open(os.path.join(directory, "songs.txt"), "w") as file:
        file.write(playlist)

if __name__ == "__main__":
    shuffle = False
    if len(sys.argv) > 2 and ((sys.argv[2]).lower() == "shuffle" or (sys.argv[2]).lower() == "true"):
        shuffle = True
    set_playlist(".", folder="playlists", filename=sys.argv[1], shuffle=shuffle)

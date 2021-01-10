import os
import pickle
import warnings
import subprocess

import numpy as np
from scipy.io import wavfile
from scipy.signal import stft

def extract_data(song_file, song_directory="./mp3-songs", data_directory="./songs-data"):
    rate, data = wavfile.read(os.path.join(song_directory, song_file))

    timedata = np.mean(data, axis=1)

    _, _, Zxx = stft(timedata, rate, nperseg=2048)

    spectrogram = np.transpose(np.abs(Zxx[1:,:]))**2
    adjusted = np.multiply(spectrogram, np.divide(np.ones(1024), np.arange(1, 1025)))
    intensity = np.sum(adjusted, axis=1)
    midpitch = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        midpitch = np.divide(np.sum(spectrogram, axis=1), intensity * 1024)

    info = {'intensity': intensity, 'midpitch': midpitch, 'sample_rate': rate}
    with open(os.path.join(data_directory, song_file[:-4]), 'wb') as datafile:
        pickle.dump(info, datafile)

def convert_songs_to_data(directory_base=".", mp3_folder="mp3-songs",
        song_folder="songs", data_folder="songs-data",
        playlist_folder="playlists", playlist_name = "playlist", append_pl=False):
    mp3_directory = os.path.join(directory_base, mp3_folder)
    song_directory = os.path.join(directory_base, song_folder)
    data_directory = os.path.join(directory_base, data_folder)
    playlist_directory = os.path.join(directory_base, playlist_folder)

    # get all mp3 files (and possibly a txt)
    files = os.listdir(mp3_directory)
    playlist = ""

    print("Extracting music data")
    track_count = len(files)
    track_count_on = 1
    for file in files:
        if file[-4:] == ".mp3":
            if os.path.exists(os.path.join(song_directory, file)) and os.path.exists(os.path.join(data_directory, file[:-4])):
                print("({}/{}) Song exists: {}".format(track_count_on, track_count, file))
                os.remove(os.path.join(mp3_directory, file))
            else:
                wav_name = file[:-4]+".wav"
                subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-i', file, wav_name], cwd=mp3_directory)
                extract_data(wav_name, mp3_directory, data_directory)
                os.rename(os.path.join(mp3_directory, file), os.path.join(song_directory, file))
                os.remove(os.path.join(mp3_directory, wav_name))
                print("({}/{}) Data extracted: {}".format(track_count_on, track_count, file))
            playlist += file[:-4] + "\n"
        else:
            print("({}/{}) Erranous file removed: {}".format(track_count_on, track_count, file))
        track_count_on += 1

    if append_pl:
        playlist_name = playlist_name + ".txt"
        with open(os.path.join(playlist_directory, playlist_name), "a") as file:
            file.write(playlist)
    else:
        i = -1
        while os.path.exists(os.path.join(playlist_directory, playlist_name + ".txt")):
            i += 1
            playlist_name = playlist_name + "_{}".format(i)
        playlist_name = playlist_name + ".txt"

        with open(os.path.join(playlist_directory, playlist_name), "w") as file:
            file.write(playlist)

    with open(os.path.join(playlist_directory, "all.txt"), "a") as file:
        file.write(playlist)

if __name__ == '__main__':
    convert_songs_to_data(mp3_folder="mp3-songs0")

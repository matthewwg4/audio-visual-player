import os
import pickle

from pydub import AudioSegment
import librosa
import numpy as np

def extract_data(song_file, song_directory="./mp3-songs", data_directory="./songs-data"):
    time_series, sample_rate = librosa.load(os.path.join(song_directory, song_file))

    cqt = np.abs(librosa.cqt(time_series, sr=sample_rate, n_bins=96))
    spectrogram = np.transpose(cqt)**2

    onset_env = librosa.onset.onset_strength(y=time_series, sr=sample_rate)
    pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sample_rate, tempo_min=12, tempo_max=150)

    _, beats = librosa.beat.beat_track(y=time_series, sr=sample_rate)
    beats = librosa.frames_to_time(beats, sr=sample_rate)

    info = {'spectrogram': spectrogram, 'pulse': pulse, 'beats': beats, 'sample_rate': sample_rate}
    with open(os.path.join(data_directory, song_file[:-4]), 'wb') as datafile:
        pickle.dump(info, datafile)

def convert_songs_to_data(directory_base=".", mp3_folder="mp3-songs",
        song_folder="songs", data_folder="songs-data",
        playlist_folder="playlists"):
    mp3_directory = os.path.join(directory_base, mp3_folder)
    song_directory = os.path.join(directory_base, song_folder)
    data_directory = os.path.join(directory_base, data_folder)
    playlist_directory = os.path.join(directory_base, playlist_folder)

    # get all mp3 files (and possibly a txt)
    files = os.listdir(mp3_directory)

    playlist = ""
    playlist_name = ""

    print("Extracting music data")
    for file in files:
        if file[-4:] == ".mp3":
            song = AudioSegment.from_mp3(os.path.join(mp3_directory, file))
            wav_name = file[:-4]+".wav"
            if os.path.exists(os.path.join(song_directory, file)):
                print("Song exists: {}".format(file))
                os.remove(os.path.join(mp3_directory, file))
            else:
                song.export(os.path.join(mp3_directory, wav_name), format="wav")
                extract_data(wav_name, mp3_directory, data_directory)
                os.rename(os.path.join(mp3_directory, file), os.path.join(song_directory, file))
                os.remove(os.path.join(mp3_directory, wav_name))
                print("Data extracted: {}".format(file))
            playlist += file[:-4] + "\n"
        elif file[-4:] == ".txt" and file != "all.txt":
            playlist_name = file

    if not playlist_name:
        i = 0
        playlist_name = "song_group_0.txt"
        while os.path.exists(os.path.join(playlist_directory, playlist_name)):
            i += 1
            playlist_name = "song_group_"+ str(i)+".txt"

    with open(os.path.join(playlist_directory, playlist_name), "w") as file:
        file.write(playlist)

    with open(os.path.join(playlist_directory, "all.txt"), "a") as file:
        file.write(playlist)

if __name__ == '__main__':
    convert_songs_to_data()

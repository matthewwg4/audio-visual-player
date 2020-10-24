import librosa
import pickle
import os
import time

import numpy as np

def main():
    for file in os.listdir("songs-wav"):
        if len(file) < 4 or file[-4:] != ".wav":
           continue
        #time0 = time.clock_gettime(time.CLOCK_MONOTONIC)
        time_series, sample_rate = librosa.load(os.path.join("songs-wav", file))
        #time1 = time.clock_gettime(time.CLOCK_MONOTONIC)
        #print("Time series: {} seconds".format(time1-time0))
        cqt = np.abs(librosa.cqt(time_series, sr=sample_rate, n_bins=96))
        #time2 = time.clock_gettime(time.CLOCK_MONOTONIC)
        #print("CQT: {} seconds".format(time2-time1))
        spectrogram = np.transpose(cqt)**2
        #end_frame = spectrogram.shape[0]
        #time3 = time.clock_gettime(time.CLOCK_MONOTONIC)
        #print("spectrogram: {} seconds".format(time3-time2))
        #spectrogram = np.divide(spectrogram, np.amax(spectrogram, axis=0))
        #time4 = time.clock_gettime(time.CLOCK_MONOTONIC)
        #print("standardize: {} seconds".format(time4-time3))
        #times = librosa.core.frames_to_time(np.arange(cqt.shape[1]), sr=sample_rate, hop_length=512)
        #time_index_ratio = len(times)/times[len(times) - 1]
        #time5 = time.clock_gettime(time.CLOCK_MONOTONIC)
        #print("time-index: {} seconds".format(time5-time4))
        #frequencies = librosa.cqt_frequencies(96, librosa.note_to_hz('C2'))
        #time7 = time.clock_gettime(time.CLOCK_MONOTONIC)
        #print("frequencies: {} seconds".format(time7-time5))
        #m_power = np.amax(spectrogram, axis=0)
        #max_power = float("-inf")
        #for f in [[0,48],[48,96]]:
        #    important_pows = m_power[f[0]:f[1]]
        #    power_avg = np.sum(important_pows)/important_pows.shape[0]
        #    # print("Sum: {}, Shape: {}, Avg: {}".format(np.sum(important_pows), important_pows.shape, power_avg))
        #    if power_avg > max_power:
        #        max_power = power_avg
        #time8 = time.clock_gettime(time.CLOCK_MONOTONIC)
        #print("max-power: {} seconds".format(time8-time7))
        onset_env = librosa.onset.onset_strength(y=time_series, sr=sample_rate)
        pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sample_rate, tempo_min=12, tempo_max=150)
        #time9 = time.clock_gettime(time.CLOCK_MONOTONIC)
        #print("pulse: {} seconds".format(time9-time8))
        _, beats = librosa.beat.beat_track(y=time_series, sr=sample_rate)
        beats = librosa.frames_to_time(beats, sr=sample_rate)
        #time10 = time.clock_gettime(time.CLOCK_MONOTONIC)
        #print("beats: {} seconds".format(time10-time9))

        info = {'spectrogram': spectrogram, 'pulse': pulse, 'beats': beats, 'sample_rate': sample_rate}
        with open(os.path.join("songs-data", file[:-4]), 'wb') as datafile:
            pickle.dump(info, datafile)
        print("Pickled: {}".format(file))
        # file = open('info-adele-hello', 'rb')
        # info = pickle.load(file)
        # file.close()
        # time11 = time.clock_gettime(time.CLOCK_MONOTONIC)
        # print("de-pickle: {} seconds".format(time11-time10))
        # print(info)

    # for file in os.listdir("playlists"):
    #     file_string = ""
    #     with open(os.path.join("playlists", file), 'r') as datafile:
    #         next_line = datafile.readline()
    #         while next_line:
    #             file_string += "{}\n".format(next_line.strip()[:-4])
    #             next_line = datafile.readline()
    #     with open(os.path.join("playlists", file), "w") as datafile:
    #         datafile.write(file_string)

if __name__ == "__main__":
    main()

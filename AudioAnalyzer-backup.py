import math

import matplotlib.pyplot as plt
import librosa
import numpy as np

class AudioAnalyzer:

    def __init__(self, freq_groups, standardize=False, use_cqt=False):

        self.freqs = freq_groups
        self.standardize = standardize
        self.use_cqt = use_cqt
        self.frequencies_index_ratio = 0  # array for frequencies
        self.time_index_ratio = 0  # array of time periods
        self.spectrogram = None  # a matrix that contains amplitude values according to frequency and time indexes
        self.end_frame = 0
        self.max_power = float("-inf")
        self.beats = None
        self.pulse = None

    def load(self, filename):

        time_series, sample_rate = librosa.load(filename)  # getting information from the file

        # getting a matrix which contains amplitude values according to frequency and time indexes

        ft = []
        if self.use_cqt:
            ft = np.abs(librosa.cqt(time_series, hop_length=512))
        else:
            ft = np.abs(librosa.stft(time_series, hop_length=512, n_fft=2048*4))

        frequencies = librosa.core.fft_frequencies(n_fft=2048*4) # getting an array of frequencies
        #weights = librosa.frequency_weighting(frequencies, kind='Z')
        #weightings = 10**librosa.A_weighting(frequencies) # getting an array of frequency weights
        weightings = 1 #10**weights
        # for i in range(200):
        #     print("{} {} {}".format(frequencies[i], weights[i], weightings[i]))

        self.spectrogram = np.multiply(np.transpose(ft)**2, weightings)
        self.end_frame = self.spectrogram.shape[0]

        if self.standardize:
            self.spectrogram = np.divide(self.spectrogram, np.amax(self.spectrogram, axis=0))

        # getting an array of time periodic
        times = librosa.core.frames_to_time(np.arange(ft.shape[1]), sr=sample_rate, hop_length=512, n_fft=(None if self.use_cqt else 2048*4))

        self.time_index_ratio = len(times)/times[len(times) - 1]

        self.frequencies_index_ratio = len(frequencies)/frequencies[len(frequencies)-1]

        m_power = np.amax(self.spectrogram, axis=0)
        for f in self.freqs:
            important_pows = m_power[int(f[0]*self.frequencies_index_ratio):int(f[1]*self.frequencies_index_ratio)]
            power_avg = np.sum(important_pows)/important_pows.shape[0]
            # print("Sum: {}, Shape: {}, Avg: {}".format(np.sum(important_pows), important_pows.shape, power_avg))
            if power_avg > self.max_power:
                self.max_power = power_avg

        # calculate times of beats
        onset_env = librosa.onset.onset_strength(y=time_series, sr=sample_rate)
        self.pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sample_rate, tempo_min=12, tempo_max=150)
        # beats = np.flatnonzero(librosa.util.localmax(pulse))
        _, beats = librosa.beat.beat_track(y=time_series, sr=sample_rate)
        self.beats = librosa.frames_to_time(beats, sr=sample_rate)


    def get_decibels(self, start, stop):

        ret = []
        beginning = min(max(0, int(start*self.time_index_ratio)), self.end_frame - 1)
        end = min(max(1, int(stop*self.time_index_ratio)), self.end_frame)
        timeslice = self.spectrogram[beginning:end]
        time_length = len(timeslice)

        for i in range(len(self.freqs)):
            f = self.freqs[i]
            freq_slice = timeslice[:, int(f[0]*self.frequencies_index_ratio):int(f[1]*self.frequencies_index_ratio)]
            power_avg = np.sum(freq_slice)/(time_length*freq_slice.shape[1])
            if power_avg < self.max_power * 0.0000000001: # 10**-10
                ret.append(-100.0)
            else:
                ret.append(10 * math.log10(power_avg / self.max_power))

        return ret

    def get_midpoint(self, start, stop):

        ret = []
        beginning = min(max(0, int(start*self.time_index_ratio)), self.end_frame - 1)
        end = min(max(1, int(stop*self.time_index_ratio)), self.end_frame)
        timeslice = self.spectrogram[beginning:end]

        total = 0
        index_weighted_total = 0
        for i in range(timeslice.shape[0]):
            for j in range(timeslice.shape[1]):
                val = timeslice[i, j]
                total += val
                index_weighted_total  +=  val*j

        midpoint = 0 if total == 0 else index_weighted_total / total / self.spectrogram.shape[1]
        avg = 0 if total == 0 else total / (timeslice.shape[0] * timeslice.shape[1])
        power = -100.0 if avg < self.max_power * 0.0000000001 else 10 * math.log10(avg / self.max_power)

        return midpoint, power

    def get_max_decibels_at_time(self, time):

        index = 0
        max = float("-inf")
        timeslice = self.spectrogram[int(round(time*self.time_index_ratio))]

        for i in range(len(self.freqs)):
            f = self.freqs[i]
            freq_slice = timeslice[int(f[0]*self.frequencies_index_ratio):int(f[1]*self.frequencies_index_ratio)]
            power_avg = np.sum(freq_slice)/freq_slice.shape[0]
            if power_avg > max:
                max = power_avg
                index = i

        if max < self.max_power * 0.0000000001: # 10**-10
            return index, -100
        else:
            return index, (10 * math.log10(max / self.max_power))

        # return ret
        #
        # index = 0
        # max = decibels[0]
        # for i in range(1, len(decibels)):
        #     val = decibels[i]
        #     if val > max:
        #         max = val
        #         index = i
        # return index, max

    def get_beats(self):
        return self.beats

    def get_pulse(self, start, stop):
        ret = []
        beginning = min(max(0, int(start*self.time_index_ratio)), self.end_frame - 1)
        end = min(max(1, int(stop*self.time_index_ratio)), self.end_frame)
        timeslice = self.pulse[beginning:end]
        time_length = len(timeslice)

        return np.sum(timeslice) / time_length

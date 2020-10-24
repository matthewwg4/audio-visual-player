import math

import matplotlib.pyplot as plt
import librosa
import numpy as np

# import pygame

# def rotate(xy, theta):
#     # https://en.wikipedia.org/wiki/Rotation_matrix#In_two_dimensions
#     cos_theta, sin_theta = math.cos(theta), math.sin(theta)
#
#     return (
#         xy[0] * cos_theta - xy[1] * sin_theta,
#         xy[0] * sin_theta + xy[1] * cos_theta
#     )
#
#
# def translate(xy, offset):
#     return xy[0] + offset[0], xy[1] + offset[1]
#
#
# def clamp(min_value, max_value, value):
#
#     if value < min_value:
#         return min_value
#
#     if value > max_value:
#         return max_value
#
#     return value


class AudioAnalyzer:

    def __init__(self, freq_groups):

        self.freqs = freq_groups
        self.frequencies_index_ratio = 0  # array for frequencies
        self.time_index_ratio = 0  # array of time periods
        self.spectrogram = None  # a matrix that contains amplitude values according to frequency and time indexes
        self.max_amplitudes = None

    def load(self, filename):

        time_series, sample_rate = librosa.load(filename)  # getting information from the file

        # getting a matrix which contains amplitude values according to frequency and time indexes
        stft = np.abs(librosa.stft(time_series, hop_length=512, n_fft=2048*4))

        self.spectrogram = np.transpose(stft)

        frequencies = librosa.core.fft_frequencies(n_fft=2048*4)  # getting an array of frequencies

        # getting an array of time periodic
        times = librosa.core.frames_to_time(np.arange(stft.shape[1]), sr=sample_rate, hop_length=512, n_fft=2048*4)

        self.time_index_ratio = len(times)/times[len(times) - 1]

        self.frequencies_index_ratio = len(frequencies)/frequencies[len(frequencies)-1]

        m_amps = np.amax(self.spectrogram, axis=0)
        self.max_amplitudes = []
        for f in self.freqs:
            self.max_amplitudes.append(np.sum(m_amps[int(f[0]*self.frequencies_index_ratio):int(f[1]*self.frequencies_index_ratio)]))


    def get_decibels(self, start, stop):

        ret = []
        timeslice = self.spectrogram[int(start*self.time_index_ratio):int(stop*self.time_index_ratio)]
        time_length = len(timeslice)

        for i in range(len(self.freqs)):
            f = self.freqs[i]
            ma = self.max_amplitudes[i]
            amps_sum = np.sum(timeslice[:, int(f[0]*self.frequencies_index_ratio):int(f[1]*self.frequencies_index_ratio)])*1.0/time_length
            if amps_sum < ma * 0.0001:
                ret.append(-80.0)
            else:
                ret.append(20 * math.log10(amps_sum / ma))

        return ret

>multiply by A_frequency_wieghting
>add on power (amplitude**2)
>divide by frequency bands
>measure inter-band instead of intra-band

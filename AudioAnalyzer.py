import math
import pickle

import numpy as np

class AudioAnalyzer:

    def __init__(self, standardize=False):

        self.freqs = [[0,96]]
        self.standardize = standardize
        self.time_index_ratio = 0  # array of time periods
        self.spectrogram = None  # a matrix that contains amplitude values according to frequency and time indexes
        self.end_frame = 0
        self.max_power = float("-inf")

    def load(self, filename):

        file = open(filename, 'rb')
        info = pickle.load(file)
        file.close()
        self.spectrogram = info['spectrogram']
        sample_rate = info['sample_rate']

        self.end_frame = self.spectrogram.shape[0]

        if self.standardize:
            self.spectrogram = np.divide(self.spectrogram, np.amax(self.spectrogram, axis=0))

        times = np.arange(self.spectrogram.shape[0]) * 512.0 / float(sample_rate)
        self.time_index_ratio = len(times)/times[len(times) - 1]

        m_power = np.amax(self.spectrogram, axis=0)
        for f in self.freqs:
            important_pows = m_power[f[0]:f[1]]
            power_avg = np.sum(important_pows)/important_pows.shape[0]
            if power_avg > self.max_power:
                self.max_power = power_avg


    def get_decibels(self, start, stop):

        ret = []
        beginning = min(max(0, int(start*self.time_index_ratio)), self.end_frame - 1)
        end = min(max(1, int(stop*self.time_index_ratio)), self.end_frame)
        timeslice = self.spectrogram[beginning:end]
        time_length = len(timeslice)

        for i in range(len(self.freqs)):
            f = self.freqs[i]
            freq_slice = timeslice[:, f[0]:f[1]]
            power_avg = np.sum(freq_slice)/(time_length*freq_slice.shape[1])
            if power_avg < self.max_power * 0.0000000001: # 10**-10
                ret.append(-100.0)
            else:
                ret.append(10 * math.log10(power_avg / self.max_power))

        return ret

    def get_midpoint(self, start, stop):

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
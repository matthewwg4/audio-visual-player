import math
import pickle

import numpy as np

class AudioAnalyzer:

    def __init__(self):

        self.time_index_ratio = 0  # index/time
        self.spectrogram = None  # array of power vals
        self.end_frame = 0
        self.max_power = float("-inf")
        self.midpitch = None

    def load(self, filename):

        file = open(filename, 'rb')
        info = pickle.load(file)
        file.close()

        self.spectrogram = info['intensity']
        self.midpitch = info['midpitch']
        sample_rate = info['sample_rate']

        self.end_frame = self.spectrogram.shape[0]

        self.time_index_ratio = sample_rate/1024

        self.max_power = np.max(self.spectrogram)
        self.midpitch = self.midpitch / np.nanmax(self.midpitch)

    def get_midpoint(self, start, stop):

        beginning = min(max(0, int(start*self.time_index_ratio)), self.end_frame - 1)
        end = min(max(beginning+1, int(stop*self.time_index_ratio)), self.end_frame)
        timeslice = self.spectrogram[beginning:end]
        pitchslice = self.midpitch[beginning:end]

        avg = np.mean(timeslice)
        midpoint = 0 if avg == 0 else np.nanmean(pitchslice)
        power = -100.0 if avg < self.max_power * 0.0000000001 else 10 * math.log10(avg / self.max_power)

        return midpoint, power

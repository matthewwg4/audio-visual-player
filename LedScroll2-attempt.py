import time
import colorsys

from AudioAnalyzer import AudioAnalyzer
from SerialCommunicator import SerialCommunicator
from AudioVisualPlayer import AudioVisualPlayer

class LEDLights:

    def __init__(self, freq_groups, songs_file='songs.txt', sample_per=0.04):

        self.serial = SerialCommunicator()
        self.player = AudioVisualPlayer(freq_groups, songs_file='songs.txt', use_cqt=True)

        self.colors = [(0,0,0)] * 25
        self.curr_color = 0
        self.sample_per = sample_per


    def setup(self):

        self.player.loadNextSong()
        self.serial.setup()

        self.current_song = wave_obj.play()

        self.start_time = time.clock_gettime(time.CLOCK_MONOTONIC)

        self.song_setup_process = Thread(target=self.loadNextSong)
        self.song_setup_process.start()

        self.last_time = self.start_time + 0.5
        return 0.5 + self.sample_per

    def update(self):

        if not self.current_song.is_playing():

            self.song_setup_process.join()
            self.current_song = self.next_song_info['song'].play()
            self.start_time = time.clock_gettime(time.CLOCK_MONOTONIC)

            self.min = -100
            self.max = 0
            self.analyzer = self.next_song_info['analyzer']
            self.last_decibels = [-100] * self.ranges

            self.song_setup_process = Thread(target=self.loadNextSong)
            self.song_setup_process.start()

            self.last_time = self.start_time + 0.5
            return 0.5 + self.sample_per


        newtime = time.clock_gettime(time.CLOCK_MONOTONIC) + 0.02
        song_time = newtime - self.start_time
        pulse = self.analyzer.get_pulse(self.last_time-self.start_time, song_time)

        self.curr_color += 0.001

        red = []
        green = []
        blue = []

        proportion = pulse

        color = colorsys.hsv_to_rgb(self.curr_color,1,proportion)
        self.colors.insert(0, color)
        self.colors.pop()
        for i in range(len(self.colors)-1, -1, -1):
            red.append(self.colors[i][0])
            green.append(self.colors[i][1])
            blue.append(self.colors[i][2])
        for color in self.colors:
            red.append(color[0])
            green.append(color[1])
            blue.append(color[2])

        self.serial.send_colors(red, green, blue)
        self.last_time = newtime

        duration = time.clock_gettime(time.CLOCK_MONOTONIC) - newtime + 0.02
        return max(self.sample_per - duration, 0)

    # End of LEDLights Class

def main():

    freq_meta_groups = [
        {'start':20, 'stop':11000, 'count':1} # all
    ]
    freq_groups = []
    for mg in freq_meta_groups:
        step = (mg['stop'] - mg['start']) / mg['count']
        for i in range(mg['count']):
            freq_groups.append([mg['start']+step*i, mg['start']+step*(i+1)])

    lights = LEDLights(freq_groups, smoothing=0, sample_per=0.04)
    delay = lights.setup()
    time.sleep(delay)
    while True:
        delay = lights.update()
        time.sleep(delay)

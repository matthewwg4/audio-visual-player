from tkinter import Tk, Canvas, Toplevel, BOTH
import time
from queue import Queue

points = [(400, 700), (438, 698), (475, 691), (510, 679), (545, 663), (576, 643), (605, 619), (631, 591), (653, 561), (671, 528), (685, 493), (695, 456), (699, 419), (699, 381), (695, 344), (685, 307), (671, 272), (653, 239), (631, 209), (605, 181), (576, 157), (545, 137), (510, 121), (475, 109), (438, 102), (400, 100), (362, 102), (325, 109), (290, 121), (255, 137), (224, 157), (195, 181), (169, 209), (147, 239), (129, 272), (115, 307), (105, 344), (101, 381), (101, 419), (105, 456), (115, 493), (129, 528), (147, 561), (169, 591), (195, 619), (224, 643), (255, 663), (290, 679), (325, 691), (362, 698)]
# inner_points = [(400, 610), (426, 608), (452, 603), (477, 595), (501, 584), (523, 570), (544, 553), (562, 534), (577, 513), (590, 489), (600, 465), (606, 439), (610, 413), (610, 387), (606, 361), (600, 335), (590, 311), (577, 287), (562, 266), (544, 247), (523, 230), (501, 216), (477, 205), (452, 197), (426, 192), (400, 190), (374, 192), (348, 197), (323, 205), (299, 216), (277, 230), (256, 247), (238, 266), (223, 287), (210, 311), (200, 335), (194, 361), (190, 387), (190, 413), (194, 439), (200, 465), (210, 489), (223, 513), (238, 534), (256, 553), (277, 570), (299, 584), (323, 595), (348, 603), (374, 608)]

class ScreenVisual(Toplevel):

    def __init__(self):
        super().__init__()

        self.colors = [("#000000",0)] * 26
        self.queue = Queue()
        # self.inner_balls = []
        # self.going_down = True

        self.initUI()

    def initUI(self):

        self.title("Screen Visualizer")
        self.geometry("800x800+550+50")

        canvas = Canvas(self, background="black")
        canvas.pack(fill=BOTH, expand=1)
        self.canvas = canvas

    def next_color(self, red, green, blue):

        val = round(max(red, green, blue)*25)
        r = int(red * 255.999)
        g = int(green * 255.999)
        b = int(blue * 255.999)
        self.colors.pop(0)
        self.colors.append(("#{:02X}{:02X}{:02X}".format(r,g,b), val))

        self.canvas.delete("all")
        fill = self.colors[0][0]
        rad = self.colors[0][1]
        self.canvas.create_oval(points[0][0]-rad, points[0][1]-rad, points[0][0]+rad, points[0][1]+rad, fill=fill)
        for i in range(1, 25):
            fill = self.colors[i][0]
            rad = self.colors[i][1]
            self.canvas.create_oval(points[i][0]-rad, points[i][1]-rad, points[i][0]+rad, points[i][1]+rad, fill=fill)
            self.canvas.create_oval(points[50-i][0]-rad, points[50-i][1]-rad, points[50-i][0]+rad, points[50-i][1]+rad, fill=fill)
        fill = self.colors[25][0]
        rad = self.colors[25][1]
        self.canvas.create_oval(points[25][0]-rad, points[25][1]-rad, points[25][0]+rad, points[25][1]+rad, fill=fill)
        
        # self.canvas.create_oval(inner_points[25][0]-10, inner_points[25][1]-10, inner_points[25][0]+10, inner_points[25][1]+10, fill=fill)
        # if self.going_down:
        #     self.going_down = rad <= self.colors[24][1]
        # elif rad < self.colors[24][1]:
        #     self.inner_balls.append([self.colors[24][0], 1])
        #     self.going_down = True

        # i = 0
        # while i < len(self.inner_balls):
        #     ball = self.inner_balls[i]
        #     if ball[1] == 25:
        #         self.canvas.create_oval(inner_points[0][0]-10, inner_points[0][1]-10, inner_points[0][0]+10, inner_points[0][1]+10, fill=ball[0])
        #         self.inner_balls.pop(i)
        #     else:
        #         self.canvas.create_oval(inner_points[25-ball[1]][0]-10, inner_points[25-ball[1]][1]-10, inner_points[25-ball[1]][0]+10, inner_points[25-ball[1]][1]+10, fill=ball[0])
        #         self.canvas.create_oval(inner_points[25+ball[1]][0]-10, inner_points[25+ball[1]][1]-10, inner_points[25+ball[1]][0]+10, inner_points[25+ball[1]][1]+10, fill=ball[0])
        #         ball[1] += 1
        #         i += 1
        
    def screen_start(self):
        self.read_queue()

    def read_queue(self):
        if not self.queue.empty():
            red, green, blue = self.queue.get()
            self.next_color(red, green, blue)
        self.after(20, self.read_queue)
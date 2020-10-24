from tkinter import Tk, Canvas, Frame, BOTH

class Example(Frame):

    def __init__(self):
        super().__init__()

        self.initUI()
        self.i = 0


    def initUI(self):

        self.master.title("Shapes")
        self.pack(fill=BOTH, expand=1)

        canvas = Canvas(self)
        canvas.create_oval(10, 10, 80, 80, outline="#f11",
            fill="#1f1", width=2)
        canvas.create_oval(110, 10, 210, 80, outline="#f11",
            fill="#1f1", width=2)
        canvas.create_rectangle(230, 10, 290, 60,
            outline="#f11", fill="#1f1", width=2)
        canvas.create_arc(30, 200, 90, 100, start=0,
            extent=210, outline="#f11", fill="#1f1", width=2)

        points = [150, 100, 200, 120, 240, 180, 210,
            200, 150, 150, 100, 200]
        canvas.create_polygon(points, outline='#f11',
            fill='#1f1', width=2)

        canvas.pack(fill=BOTH, expand=1)
        self.canvas = canvas
        self.canvas.after(1000, self.onTimer)

    def updateUI(self):
        self.canvas.delete("all")
        if self.i % 2 == 0:
            self.canvas.create_rectangle(10, 10, 290, 200,
                outline="#000", fill="#000", width=2)
        else:
            self.canvas.create_rectangle(10, 10, 290, 200,
                outline="#fff", fill="#fff", width=2)

        self.canvas.pack(fill=BOTH, expand=1)
        self.i += 1

    def onTimer(self):
        self.updateUI()
        self.canvas.after(1000, self.onTimer)


def main():

    root = Tk()
    ex = Example()
    root.geometry("330x220+300+300")
    root.mainloop()


if __name__ == '__main__':
    main()

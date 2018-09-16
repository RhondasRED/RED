#Recalculate DVH (RED) program to display an EQD2 DVH to allow for alpha/beta ratio testing
#Author = Rhonda Flynn
#Creation Date = June 2018

from tkinter import *
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg


class initialfunction:

    def __init__(self, window):
        self.window = window
        self.window.title("Recalculate to Equivalent Dose (RED)")
        self.window.iconbitmap("C:/Users/Owner/Documents/Rlogo2.ico")
        self.label1 = Label(window, text="Dose per fraction in Gy")
        self.label2 = Label(window, text=" Alpha/Beta 1")
        self.label3 = Label(window, text=" Alpha/Beta 2")
        self.label4 = Label(window, text=" Type 1 for Dose in % or 2 for Dose in Gy")
        self.label5 = Label(window, text="Volume of ROI in cc")
        self.box1 = Entry(window)
        self.box2 = Entry(window)
        self.box3 = Entry(window)
        self.box4 = Entry(window)
        self.box5 = Entry(window)
        self.button1 = Button(window, text="Calculate", command=self.plot)
        self.label1.grid(row=0, sticky=E)
        self.label2.grid(row=1, sticky=E)
        self.label3.grid(row=2, sticky=E)
        self.label4.grid(row=3, sticky=E)
        self.label5.grid(row=4, sticky=E)
        self.box1.grid(row=0, column=1)
        self.box2.grid(row=1, column=1)
        self.box3.grid(row=2, column=1)
        self.box4.grid(row=3, column=1)
        self.box5.grid(row=4, column=1)
        self.button1.grid(row=5, column=1)

    def plot(self):
        d = float(self.box1.get())
        ab1 = float(self.box2.get())
        ab2 = float(self.box3.get())
        unit = float(self.box4.get())

        #read in excel sheet and specify from where data is to be taken#
        if unit == 1:
            wb1 = pd.read_excel(r"C:/Users/Owner/Desktop/RED.xlsx", skiprows='0-208', header=209,
                           sheet_name='REDalphabeta', na_values=['NA'])
            a1 = wb1.loc[:, "Dose"]
            a2 = wb1.loc[:, "Volume"]

        elif unit ==2:
            wb2 = pd.read_excel(r"C:/Users/Owner/Desktop/RED.xlsx", skiprows='0-4', skipfooter=209 ,header=5,
                            sheet_name='REDalphabeta', na_values=['NA'])
            a1 = wb2.loc[:, "Dose"]
            a2 = wb2.loc[:, "Volume"]

        x1 = np.array((d + ab1) / (int(2) + ab1))
        eqd21 = x1 * a1
        x2 = np.array((d + ab2) / (int(2) + ab2))
        eqd22 = x2 * a1

        fig = Figure()
        ax = fig.add_subplot(111)
        ax.plot(eqd21, a2, c='m')
        ax.plot(eqd22, a2, c='b')
        ax.legend([" a/b 1", "a/b 2"])
        ax.set_ylabel("Volume cc", fontsize=14)
        ax.set_xlabel("Dose Gy", fontsize=14)
        ax.set_axisbelow(True)
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.xaxis.grid(color='gray', linestyle='dashed')


        canvas = FigureCanvasTkAgg(fig, master=self.window)
        canvas.get_tk_widget().grid(row=6, column=3)
        canvas.draw()

        toolbarFrame = Frame(master=self.window)
        toolbarFrame.grid(row=10, column=3)
        toolbar = NavigationToolbar2TkAgg(canvas, toolbarFrame)
        toolbar.draw()

window = Tk()
start = initialfunction(window)
window.mainloop()

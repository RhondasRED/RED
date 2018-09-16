#Recalculate DVH (RED) program to display an EQD2 DVH for the addition of RT plans
#Author = Rhonda Flynn
#Creation Date = July 2018

from tkinter import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from mpldatacursor import datacursor

class initialfunction:

    def __init__(self, window):
        self.window = window
        self.window.title("Recalculate Equivalant Dose")
        self.window.iconbitmap("C:/Users/Owner/Documents/Rlogo2.ico")
        self.label1 = Label(window, text=" Plan 1 Dose per fraction in Gy")
        self.label2 = Label(window, text=" Plan 2 Dose per fraction in Gy")
        self.label3 = Label(window, text=" Organ Alpha/Beta")
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

        #T = Text(self.window, height=4, width=22)
        #T.grid(row=6, column=0)
       # OARab = "Suggested α/β values: " \
        #        "Spinal Cord = 1.4Gy" \
        #        " Un-involved Breast Tissue = 4Gy" \
        #        "Lung Tissue = 2.5Gy " \
        #        "Heart Tissue = 2.5Gy\n"
        #T.insert(END, OARab)

    def plot(self):

        #Take inputs from user#
        d1 = float(self.box1.get())
        d2 = float(self.box2.get())
        ab = float(self.box3.get())
        unit = float(self.box4.get())
        vol = float(self.box5.get())

        #read in excel sheet and specify from where data is to be taken#
        if unit == 1:
            wb1 = pd.read_excel(r"C:/Users/Owner/Desktop/RED.xlsx", skiprows='0-209', header=210,
                           sheet_name='REDaddplans', na_values=['NA'])
            a1 = wb1.loc[:, "Dose 1"]
            a2 = wb1.loc[:, "Volume 1"]
            b1 = wb1.loc[:, "Dose 2"]
            b2 = wb1.loc[:, "Volume 2"]
        elif unit ==2:
            wb2 = pd.read_excel(r"C:/Users/Owner/Desktop/RED.xlsx", skiprows='0-4', skipfooter=209 ,header=5,
                            sheet_name='REDaddplans', na_values=['NA'])
            a1 = wb2.loc[:, "Dose 1"]
            a2 = wb2.loc[:, "Volume 1"]
            b1 = wb2.loc[:, "Dose 2"]
            b2 = wb2.loc[:, "Volume 2"]

        #recalculate biologically using EQD2 formulism#
        x1 = np.array((d1 + ab) / (int(2) + ab))
        eqd21 = x1 * a1
        x2 = np.array((d2 + ab) / (int(2) + ab))
        eqd22 = x2 * b1

        #plot the curves#
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.plot(eqd21, a2, c='m')
        ax.plot(eqd22, b2, c='b')

        #get values from plan1 graph#
        line1 = ax.lines[0]
        line1.get_xydata()
        xdat1 = eqd21
        fp1 = xdat1[::-1]  #reverses x values to match reversed y values in array#
        ydat1 = line1.get_ydata()
        xp1 = ydat1[::-1] #reverses y values from decreasng to increasing so interpolation function can work#

        #get values from plan2 graph#
        line2 = ax.lines[1]
        line2.get_xydata()
        xdat2 = eqd22
        fp2 = xdat2[::-1]  #reverses x values to match reversed y values in array#
        ydat2 = line2.get_ydata()
        xp2 = ydat2[::-1] #reverses y values from decreasng to increasing so interpolation function can work#

        #set graph gui parameters#
        if unit == 1:
            ax.set_ylabel("Volume cc", fontsize=14)
            ax.set_xlabel("Dose Gy", fontsize=14)
        elif unit ==2:
            ax.set_ylabel("Volume cc", fontsize=14)
            ax.set_xlabel("Dose %", fontsize=14)
        ax.set_axisbelow(True)
        datacursor()
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.xaxis.grid(color='gray', linestyle='dashed')

        #set volume array to use for dose interpolation#
        array = np.linspace(0, vol, 1000, endpoint=False)
        inter1 = np.interp([array], xp1, fp1)#interpolation of plan1 dose
        reshapeinter1 = np.reshape(inter1,(1000,1))
        inter2 = np.interp([array], xp2, fp2)#interpolation of plan2 dose
        reshapeinter2 = np.reshape(inter2, (1000, 1))
        interxvalues = reshapeinter1 + reshapeinter2 #adding plan1 and plan2 dose
        reshapearray = np.reshape(array,(1000,1))#array of specified %volume in 0.1% intervals
        ax.plot(interxvalues, reshapearray, c='y')
        ax.legend(["Plan 1 EQD2", "Plan 2 EQD2", "Plan 1+2 EQD2"])

        canvas = FigureCanvasTkAgg(fig, master=self.window)
        canvas.get_tk_widget().grid(row=8, column=5)
        canvas.draw()
        plt.show()

        toolbarFrame = Frame(master=self.window)
        toolbarFrame.grid(row=22, column=5)
        toolbar = NavigationToolbar2TkAgg(canvas, toolbarFrame)
        toolbar.draw()

window = Tk()
start = initialfunction(window)
window.mainloop()

#!/usr/bin/env python
"""Calculate dose volume histogram (DVH) using EQD2 from DICOM RT Structure/Dose data
 and use to add up to 4 dose files from 2 plans i.e. re-treatment"""
# Author Rhonda Flynn
# Copyright (c) 2011-2016 Aditya Panchal: "dicompyler-core" See the file license.txt available at
# https://github.com/dicompyler/dicompyler-core/

from dicompylercore import dicomparser, dvh, dvhcalc
import numpy as np
from tkinter import *
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpldatacursor import datacursor
from tkinter import ttk
from tkinter import filedialog

class RED:
    #initiate the input parameter window
    def __init__(self, window):
        print("Welcome to RED")
        print("Please enter your data into the input parameter window")
        print("When you are ready click on the 'Calculate' button")
        #design of input parameter window
        self.window = window
        self.window.title("Input Parameters")
        #self.window.iconbitmap("C:/Users/Owner/Downloads/RED-master/RED-master/REDlogo.png") #import RED logo
        # self.window["bg"]="red" #change input window background colour, default grey

        #initialisation of inputs
        self.label1 = Label(window, text=" Plan 1 dose per fraction")
        self.label2 = Label(window, text=" Plan 2 dose per fraction")
        self.label3 = Label(window, text=" Organ Alpha/Beta")
        self.label4 = Label(window)
        self.label5 = Label(window)
        self.label6 = Label(window)
        self.label7 = Label(window)
        self.label8 = Label(window)
        self.label9 = Label(window)
        self.label10 = Label(window)
        self.label11 = Label(window)
        self.label12 = Label(window)
        self.label13 = Label(window)
        self.label14 = Label(window, text="ROI (exact name from TPS, case sensitive)")  #input is case sensitive
        self.label15 = Label(window)
        self.label16 = Label(window)
        self.label17 = Label(window)
        self.label18 = Label(window)
        self.label19 = Label(window)
        self.label20 = Label(window)
        self.label21 = Label(window)
        self.label22 = Label(window)
        self.label23 = Label(window, text="Quantity of DICOM dose files in Plan 1")
        self.label24 = Label(window, text="Quantity of DICOM dose files in Plan 2")
        self.box1 = Entry(window)
        self.box2 = Entry(window)
        self.box3 = Entry(window)
        self.box4 = Entry(window)
        self.box5 = Entry(window)
        self.box6 = Entry(window)
        self.button1 = Button(window, text="Calculate", command=self.plot)
        self.button2 = ttk.Button(self.label4, text="Browse for Plan1 RD.dcm #1", command=self.fileDialog1)
        self.button3 = ttk.Button(self.label5, text="Browse for Plan1 RD.dcm #2", command=self.fileDialog2)
        self.button4 = ttk.Button(self.label6, text="Browse for Plan1 RD.dcm #3", command=self.fileDialog3)
        self.button5 = ttk.Button(self.label7, text="Browse for Plan1 RD.dcm #4", command=self.fileDialog4)
        self.button6 = ttk.Button(self.label8, text="Browse for struture file RS.dcm", command=self.fileDialog5)
        self.button7 = ttk.Button(self.label15, text="Browse for Plan2 RD.dcm #1", command=self.fileDialog6)
        self.button8 = ttk.Button(self.label16, text="Browse for Plan2 RD.dcm #2", command=self.fileDialog7)
        self.button9 = ttk.Button(self.label17, text="Browse for Plan2 RD.dcm #3", command=self.fileDialog8)
        self.button10 = ttk.Button(self.label18, text="Browse for Plan2 RD.dcm #4", command=self.fileDialog9)
        self.button11 = ttk.Button(self.label19, text="Plan 1")
        self.button12 = ttk.Button(self.label20, text="Plan 2")
        self.button13 = ttk.Button(self.label21, text="Plan 1")
        self.button14 = ttk.Button(self.label22, text="Plan 2")

        #labeling of inputs
        self.label1.grid(row=0, sticky=E)
        self.label2.grid(row=1, sticky=E)
        self.label3.grid(row=2, sticky=E)
        self.label14.grid(row=3, sticky=E)
        self.label23.grid(row=4, sticky=E)
        self.label24.grid(row=5, sticky=E)
        self.label4.grid(row=6)
        self.label5.grid(row=7)
        self.label6.grid(row=8)
        self.label7.grid(row=9)
        self.label8.grid(row=16)
        self.label15.grid(row=11)
        self.label16.grid(row=12)
        self.label17.grid(row=13)
        self.label18.grid(row=14)
        self.label19.grid(row=15)

        #assigning labels to boxes & correct ordering
        self.box1.grid(row=0, column=1)
        self.box2.grid(row=1, column=1)
        self.box3.grid(row=2, column=1)
        self.box4.grid(row=3, column=1)
        self.box5.grid(row=4, column=1)
        self.box6.grid(row=5, column=1)

        #assigning labels to buttons & correct ordering
        self.button1.grid(row=18, column=1)  # calculate button
        self.button2.grid(row=6, column=1)  # choose dose file
        self.button3.grid(row=7, column=1)  # choose dose file
        self.button4.grid(row=8, column=1)  # choose dose file
        self.button5.grid(row=9, column=1)  # choose dose file
        self.button6.grid(row=16, column=1)  # choose structure file
        self.button7.grid(row=11, column=2)
        self.button8.grid(row=12, column=1)
        self.button9.grid(row=13, column=1)
        self.button10.grid(row=14, column=1)


    #collection of DICOM files from user based on how many files user has defined for each plan
    def fileDialog1(self):
        self.filename1 = filedialog.askopenfilename(initialdir="/", title="Select A File",
                                                    filetype=(("dicom", "*.dcm"), ("All Files", "*.*")))
        self.label4 = ttk.Label(self.label4, text="")
        self.label4.grid(row=6, sticky=E)
        self.label4.configure(text=self.filename1)

    def fileDialog2(self):
        plan1files = float(self.box5.get())
        if plan1files >= 2:
            self.filename2 = filedialog.askopenfilename(initialdir="/", title="Select A File",
                                                        filetype=(("dicom", "*.dcm"), ("All Files", "*.*")))
            self.label5 = ttk.Label(self.label5, text="")
            self.label5.grid(row=7, sticky=E)
            self.label5.configure(text=self.filename2)
        else:
            print("To add a second dose file please make sure the Plan1 box = 2")

    def fileDialog3(self):
        plan1files = float(self.box5.get())
        if plan1files >= 3:
            self.filename3 = filedialog.askopenfilename(initialdir="/", title="Select A File",
                                                        filetype=(("dicom", "*.dcm"), ("All Files", "*.*")))
            self.label6 = ttk.Label(self.label6, text="")
            self.label6.grid(row=8, sticky=E)
            self.label6.configure(text=self.filename3)
        else:
            print("To add a third dose file please make sure the Plan1 box = 3")

    def fileDialog4(self):
        plan1files = float(self.box5.get())
        if plan1files >= 4:
            self.filename4 = filedialog.askopenfilename(initialdir="/", title="Select A File",
                                                        filetype=(("dicom", "*.dcm"), ("All Files", "*.*")))
            self.label7 = ttk.Label(self.label7, text="")
            self.label7.grid(row=9, sticky=E)
            self.label7.configure(text=self.filename4)
        else:
            print("To add a fourth dose file please make sure the Plan1 box = 4")

    def fileDialog5(self):  # structure file
        self.filename5 = filedialog.askopenfilename(initialdir="/", title="Select A File",
                                                    filetype=(("dicom", "*.dcm"), ("All Files", "*.*")))
        self.label8 = ttk.Label(self.label8, text="")
        self.label8.grid(row=16, sticky=E)
        self.label8.configure(text=self.filename5)

    def fileDialog6(self):
        self.filename6 = filedialog.askopenfilename(initialdir="/", title="Select A File",
                                                    filetype=(("dicom", "*.dcm"), ("All Files", "*.*")))
        self.label15 = ttk.Label(self.label15, text="")
        self.label15.grid(row=11, sticky=E)
        self.label15.configure(text=self.filename6)

    def fileDialog7(self):
        plan2files = float(self.box6.get())
        if plan2files >= 2:
            self.filename7 = filedialog.askopenfilename(initialdir="/", title="Select A File",
                                                        filetype=(("dicom", "*.dcm"), ("All Files", "*.*")))
            self.label16 = ttk.Label(self.label16, text="")
            self.label16.grid(row=12, sticky=E)
            self.label16.configure(text=self.filename7)
        else:
            print("To add a second dose file please make sure the Plan2 box = 2")

    def fileDialog8(self):
        plan2files = float(self.box6.get())
        if plan2files >= 3:
            self.filename8 = filedialog.askopenfilename(initialdir="/", title="Select A File",
                                                        filetype=(("dicom", "*.dcm"), ("All Files", "*.*")))
            self.label17 = ttk.Label(self.label17, text="")
            self.label17.grid(row=13, sticky=E)
            self.label17.configure(text=self.filename8)
        else:
            print("To add a third dose file please make sure the Plan2 box = 3")

    def fileDialog9(self):
        plan2files = float(self.box6.get())
        if plan2files >= 4:
            self.filename9 = filedialog.askopenfilename(initialdir="/", title="Select A File",
                                                        filetype=(("dicom", "*.dcm"), ("All Files", "*.*")))
            self.label18 = ttk.Label(self.label18, text="")
            self.label18.grid(row=14, sticky=E)
            self.label18.configure(text=self.filename9)
        else:
            print("To add a fourth dose file please make sure the Plan2 box = 4")

    #plotting of EQD2 recalculated plan 1 and 2 individually
    def plot(self):

        #retrieve plan data & design DVH window
        plan1files = float(self.box5.get())
        plan2files = float(self.box6.get())
        self.newWindow = Toplevel(self.window) #initiate new window for summed DVH
        self.newWindow.title("Recalculated DVH")
        #self.newWindow.iconbitmap("C:/Users/Owner/Documents/Rlogo2.ico")

        rtssfile1 = self.filename5 #structure file
        RTss1 = dicomparser.DicomParser(rtssfile1) #read through structure file
        RTstructures1 = RTss1.GetStructures() #get each individual structure information

        #at least one dose file required for plan 1 and plan 2
        rtdosefile1 = self.filename1
        rtdosefile5 = self.filename6
        #conditional statements for multiple dose file input
        if plan1files >= 2:
            rtdosefile2 = self.filename2
        if plan1files >= 3:
            rtdosefile3 = self.filename3
        if plan1files >= 4:
            rtdosefile4 = self.filename4
        if plan2files >= 2:
            rtdosefile6 = self.filename7
        if plan2files >= 3:
            rtdosefile7 = self.filename8
        if plan2files >= 4:
            rtdosefile8 = self.filename9

        #structure to be analysed
        enteredtext = str(self.box4.get())

        #EQD2 parameters
        dpf1 = float(self.box1.get()) #plan 1 dose per fraction
        dpf2 = float(self.box2.get()) #plan 2 dose per fraction
        abratio = float(self.box3.get())  # tissue-specific alpha/beta ratio

        #EQD2 equation
        x1 = np.array((dpf1 + abratio) / (float(2.0) + abratio))
        x2 = np.array((dpf2 + abratio) / (float(2.0) + abratio))

        # Generation of the calculated DVHs
        #initiation of empty arrays to fill with correct structure data
        calcdvhs1 = {}
        calcdvhs2 = {}
        calcdvhs3 = {}
        calcdvhs4 = {}
        calcdvhs5 = {}
        calcdvhs6 = {}
        calcdvhs7 = {}
        calcdvhs8 = {}

        print("RED is calculating your EQD2 DVH....")
        print("Please wait, this could take a few moments")
        #iterate through dose file 1 to find correct stucture data
        for key, structure in RTstructures1.items():
            calcdvhs1[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile1, key)
            if (key in calcdvhs1) and (structure['name'] == enteredtext) and (
                    len(calcdvhs1[key].counts) and calcdvhs1[key].counts[0] != 0):
                print('1st Plan 1 DVH found for ' + structure['name'])
                data1 = np.array(calcdvhs1[key].bins) * x1
                lastdata1 = data1[-1]
                vola = calcdvhs1[key].counts * 100 / calcdvhs1[key].counts[0]

        # iterate through dose file 2 to find correct stucture data
        if plan1files >= 2:
            for key, structure in RTstructures1.items():
                calcdvhs2[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile2, key)
                if (key in calcdvhs2) and (structure['name'] == enteredtext) and (
                        len(calcdvhs2[key].counts) and calcdvhs2[key].counts[0] != 0):
                    print('2nd Plan 1 DVH found for ' + structure['name'])
                    data2 = np.array(calcdvhs2[key].bins) * x1
                    lastdata2 = data2[-1]
                    volb = calcdvhs2[key].counts * 100 / calcdvhs2[key].counts[0]

        # iterate through dose file 3 to find correct stucture data
        if plan1files >= 3:
            for key, structure in RTstructures1.items():
                calcdvhs3[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile3, key)
                if (key in calcdvhs3) and (structure['name'] == enteredtext) and (
                        len(calcdvhs3[key].counts) and calcdvhs3[key].counts[0] != 0):
                    print('3rd Plan 1 DVH found for ' + structure['name'])
                    data3 = np.array(calcdvhs3[key].bins) * x1
                    lastdata3 = data3[-1]
                    volc = calcdvhs3[key].counts * 100 / calcdvhs3[key].counts[0]

        # iterate through dose file 4 to find correct stucture data
        if plan1files >= 4:
            for key, structure in RTstructures1.items():
                calcdvhs4[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile4, key)
                if (key in calcdvhs4) and (structure['name'] == enteredtext) and (
                        len(calcdvhs4[key].counts) and calcdvhs4[key].counts[0] != 0):
                    print('4th Plan 1 DVH found for ' + structure['name'])
                    data4 = np.array(calcdvhs4[key].bins) * x1
                    lastdata4 = data4[-1]
                    vold = calcdvhs4[key].counts * 100 / calcdvhs4[key].counts[0]

        # iterate through dose file 5 to find correct stucture data
        for key, structure in RTstructures1.items():
            calcdvhs5[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile5, key)
            if (key in calcdvhs5) and (structure['name'] == enteredtext) and (
                    len(calcdvhs5[key].counts) and calcdvhs5[key].counts[0] != 0):
                print('1st Plan 2 DVH found for ' + structure['name'])
                data5 = np.array(calcdvhs5[key].bins) * x2
                lastdata5 = data5[-1]
                vole = calcdvhs5[key].counts * 100 / calcdvhs5[key].counts[0]

        # iterate through dose file 6 to find correct stucture data
        if plan2files >= 2:
            for key, structure in RTstructures1.items():
                calcdvhs6[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile6, key)
                if (key in calcdvhs6) and (structure['name'] == enteredtext) and (
                        len(calcdvhs6[key].counts) and calcdvhs6[key].counts[0] != 0):
                    print('2nd Plan 2 DVH found for ' + structure['name'])
                    data6 = np.array(calcdvhs6[key].bins) * x2
                    lastdata6 = data6[-1]
                    volf = calcdvhs6[key].counts * 100 / calcdvhs6[key].counts[0]

        # iterate through dose file 7 to find correct stucture data
        if plan2files >= 3:
            for key, structure in RTstructures1.items():
                calcdvhs7[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile7, key)
                if (key in calcdvhs7) and (structure['name'] == enteredtext) and (
                        len(calcdvhs7[key].counts) and calcdvhs7[key].counts[0] != 0):
                    print('3rd Plan 2 DVH found for ' + structure['name'])
                    data7 = np.array(calcdvhs7[key].bins) * x2
                    lastdata7 = data7[-1]
                    volg = calcdvhs7[key].counts * 100 / calcdvhs7[key].counts[0]

        # iterate through dose file 8 to find correct stucture data
        if plan2files >= 4:
            for key, structure in RTstructures1.items():
                calcdvhs8[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile8, key)
                if (key in calcdvhs8) and (structure['name'] == enteredtext) and (
                        len(calcdvhs8[key].counts) and calcdvhs8[key].counts[0] != 0):
                    print('4th Plan 2 DVH found for ' + structure['name'])
                    data8 = np.array(calcdvhs8[key].bins) * x2
                    lastdata8 = data8[-1]
                    volh = calcdvhs8[key].counts * 100 / calcdvhs8[key].counts[0]

        #initiation of DVH window
        fig = Figure()
        ax = fig.add_subplot(111)

        #addition of plan 1 dose data
        if plan1files == 1:
            totaldose1 = lastdata1
        if plan1files == 2:
            totaldose1 = lastdata1 + lastdata2
        if plan1files == 3:
            totaldose1 = lastdata1 + lastdata2 + lastdata3
        if plan1files == 4:
            totaldose1 = lastdata1 + lastdata2 + lastdata3 + lastdata4

        #addition of plan 2 dose data
        if plan2files == 1:
            totaldose2 = lastdata5
        if plan2files == 2:
            totaldose2 = lastdata5 + lastdata6
        if plan2files == 3:
            totaldose2 = lastdata5 + lastdata6 + lastdata7
        if plan2files == 4:
            totaldose2 = lastdata5 + lastdata6 + lastdata7 + lastdata8

        #conditional statements for plan 1 based on number of dose files
        #definition of volume and dose data
        if plan1files == 1:
            y = vola #volume data
            y1len = len(y)
            x = np.linspace(0, totaldose1, num=y1len) #dose data
        elif plan1files == 2:
            interyvaluesplan1b = np.concatenate((vola, volb), axis=0)#summed volume data
            sorty21 = np.sort(interyvaluesplan1b) #sorted volume data array in ascending order
            vol21 = sorty21[::-1]#volume data array reversed to descending order
            y = vol21 #volume data
            y1len = len(y)
            x = np.linspace(0, totaldose1, num=y1len) #dose data
        elif plan1files == 3:
            interyvalues1plan1a = np.concatenate((vola, volb), axis=0)
            interyvaluesplan1c = np.concatenate((interyvalues1plan1a, volc), axis=0) #sumed volume data
            sorty31 = np.sort(interyvaluesplan1c)#sorted volume data array in ascending order
            vol31 = sorty31[::-1]#volume data array reversed to descending order
            y = vol31 #volume data
            y1len = len(y)
            x = np.linspace(0, totaldose1, num=y1len) #dose data
        elif plan1files == 4:
            interyvalues1plan1b = np.concatenate((vola, volb), axis=0)
            interyvalues2plan1a = np.concatenate((volc, vold), axis=0)
            interyvaluesplan1d = np.concatenate((interyvalues1plan1b, interyvalues2plan1a), axis=0) #summed volume data
            sorty41 = np.sort(interyvaluesplan1d) #sorted volume data array in ascending order
            vol41 = sorty41[::-1] #volume data array reversed to descending order
            y = vol41
            y1len = len(y)
            x = np.linspace(0, totaldose1, num=y1len) #dose data
        else:
            print("please check code starting at line 367")

        if plan2files == 1:
            b = vole #volume data
            blen = len(b)
            a = np.linspace(0, totaldose2, num=blen) #dose data

        elif plan2files == 2:
            interyvaluesplan2b = np.concatenate((vole, volf), axis=0) #summed volume data
            sorty22 = np.sort(interyvaluesplan2b)# sorted volume data array in ascending order
            vol22 = sorty22[::-1] #volume data array reversed to descending order
            b = vol22
            blen = len(b)
            a = np.linspace(0, totaldose2, num=blen) #dose data

        elif plan2files == 3:
            interyvalues1plan2a = np.concatenate((vole, volf), axis=0)
            interyvaluesplan2c = np.concatenate((interyvalues1plan2a, volg), axis=0)#summed volume data
            sorty32 = np.sort(interyvaluesplan2c) #sorted volume data array in ascending order
            vol32 = sorty32[::-1] #volume data array reversed to descending order
            b = vol32
            blen = len(b)
            a = np.linspace(0, totaldose2, num=blen) #dose data

        elif plan2files == 4:
            interyvalues1plan2b = np.concatenate((vole, volf), axis=0)
            interyvalues2plan2a = np.concatenate((volg, volh), axis=0)
            interyvaluesplan2d = np.concatenate((interyvalues1plan2b, interyvalues2plan2a), axis=0) #summed volume data
            sorty42 = np.sort(interyvaluesplan2d) #sorted volume data array in ascending order
            vol42 = sorty42[::-1] # volume data array reversed to descending order
            b = vol42
            blen = len(b)
            a = np.linspace(0, totaldose2, num=blen) #dose data
        else:
            print("please check code starting at line 398")

        #plot plan 1 and plan 2 re-calculated DVH
        ax.plot(x, y, c='b')
        ax.plot(a, b, c='g')
        array = np.linspace(0, 100, 9000, endpoint=False)
        # get values from plan1 graph
        line1 = ax.lines[0]
        line1.get_xydata()
        xdat1 = line1.get_xdata() #get x data
        fp1 = xdat1[::-1]  # reverses x values to match reversed y values in array#
        ydat1 = line1.get_ydata() #get y data
        xp1 = ydat1[::-1]  # reverses y values from decreasng to increasing so interpolation function can work

        # get values from plan2 graph
        line2 = ax.lines[1]
        line2.get_xydata()
        xdat2 = line2.get_xdata() #get xdata
        fp2 = xdat2[::-1]  # reverses x values to match reversed y values in array
        ydat2 = line2.get_ydata() #get y data
        xp2 = ydat2[::-1]  # reverses y values from decreasng to increasing so interpolation function can work

        # set volume array to use for dose interpolation
        inter1 = np.interp([array], xp1, fp1)  # interpolation of plan1 dose
        reshapeinter1 = np.reshape(inter1, (9000, 1))
        inter2 = np.interp([array], xp2, fp2)  # interpolation of plan2 dose
        reshapeinter2 = np.reshape(inter2, (9000, 1))
        xvalues = reshapeinter1 + reshapeinter2  # adding plan1 and plan2 dose
        reshapearray = np.reshape(array, (9000, 1))  # array of specified %volume intervals

        #define strings
        dpf12 = str(dpf1)
        dpf21 = str(dpf2)
        abdisplay = str(abratio)

        #plot summed re-calculated DVH in seperate window
        plt.plot(xvalues, reshapearray, c='r')
        plt.title("Recalculated Summed DVH")
        # plt.iconbitmap("C:/Users/Owner/Documents/Rlogo2.ico")
        plt.title(
            "Summed EQD2 DVH for " + enteredtext + " a/b=" + abdisplay + " dpf Plan 1=" + dpf12 + " dpf Plan 2=" + dpf21)
        ax.legend(["Plan 1", "Plan 2"])
        ax.set_title(
            "EQD2 DVH for " + enteredtext + " a/b=" + abdisplay + " dpf Plan 1=" + dpf12 + " dpf Plan 2=" + dpf21)
        ax.set_ylabel("Volume %", fontsize=14)
        ax.set_xlabel("EQD2 Gy", fontsize=14)
        plt.legend(["Plan 1 + 2"])
        plt.ylabel("Volume %", fontsize=14)
        plt.xlabel("EQD2 Gy", fontsize=14)
        ax.set_axisbelow(True)

        #design of summed dvh
        plt.grid(color='gray', linestyle='dashed')
        datacursor()
        ax.yaxis.grid(color='gray', linestyle='dashed')
        ax.xaxis.grid(color='gray', linestyle='dashed')

        #draw sumed DVH
        canvas = FigureCanvasTkAgg(fig, master=self.newWindow)
        canvas.get_tk_widget().grid(row=10)
        canvas.draw()
        plt.show()

        #initiate toolbar for analysis
        toolbarFrame = Frame(master=self.newWindow)
        toolbarFrame.grid(row=20)
        toolbar = NavigationToolbar2Tk(canvas, toolbarFrame)
        toolbar.draw()

window = Tk()
start = RED(window)
window.mainloop()

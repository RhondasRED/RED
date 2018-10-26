#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dvhcalc.py
"""Calculate dose volume histogram (DVH) from DICOM RT Structure/Dose data."""
# Copyright (c) 2016 gluce
# Copyright (c) 2011-2016 Aditya Panchal
# Copyright (c) 2010 Roy Keyes
# This file is part of dicompyler-core, released under a BSD license.
#    See the file license.txt included with this distribution, also
#    available at https://github.com/dicompyler/dicompyler-core/

from __future__ import division
import pylab as pl
from dicompylercore import dicomparser, dvh, dvhcalc
import sys
import numpy as np
import numpy.ma as ma
import matplotlib.path
from six import iteritems
import logging
logger = logging.getLogger('dicompylercore.dvhcalc')
import xlsxwriter
import os
import pydicom as dicom
from tkinter import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpldatacursor import datacursor
import pyeqd2 as eqd
from tkinter import ttk
from tkinter import filedialog


def get_dvh(structure, dose, roi, limit=None, callback=None):
    """Calculate a cumulative DVH in Gy from a DICOM RT Structure Set & Dose.
    Parameters
    ----------
    structure : pydicom Dataset
        DICOM RT Structure Set used to determine the structure data.
    dose : pydicom Dataset
        DICOM RT Dose used to determine the dose grid.
    roi : int
        The ROI number used to uniquely identify the structure in the structure
        set.
    limit : int, optional
        Dose limit in cGy as a maximum bin for the histogram.
    callback : function, optional
        A function that will be called at every iteration of the calculation.
    """
    from dicompylercore import dicomparser
    rtss = dicomparser.DicomParser(structure)
    rtdose = dicomparser.DicomParser(dose)
    structures = rtss.GetStructures()
    s = structures[roi]
    s['planes'] = rtss.GetStructureCoordinates(roi)
    s['thickness'] = rtss.CalculatePlaneThickness(s['planes'])
    hist = calculate_dvh(s, rtdose, limit, callback)
    return dvh.DVH(counts=hist,
                   bins=(np.arange(0, 2) if (hist.size == 1) else
                         np.arange(0, hist.size + 1) / 100),
                   dvh_type='differential',
                   dose_units='gy',
                   name=s['name']
                   ).cumulative


def calculate_dvh(structure, dose, limit=None, callback=None):
    """Calculate the differential DVH for the given structure and dose grid.
    Parameters
    ----------
    structure : dict
        A structure (ROI) from an RT Structure Set parsed using DicomParser
    dose : DicomParser
        A DicomParser instance of an RT Dose
    limit : int, optional
        Dose limit in cGy as a maximum bin for the histogram.
    callback : function, optional
        A function that will be called at every iteration of the calculation.
    """
    planes = structure['planes']
    logger.debug(
        "Calculating DVH of %s %s", structure['id'], structure['name'])

    # Create an empty array of bins to store the histogram in cGy
    # only if the structure has contour data or the dose grid exists
    if ((len(planes)) and ("PixelData" in dose.ds)):

        # Get the dose and image data information
        dd = dose.GetDoseData()
        id = dose.GetImageData()

        # Generate a 2d mesh grid to create a polygon mask in dose coordinates
        # Code taken from Stack Overflow Answer from Joe Kington:
        # https://stackoverflow.com/q/3654289/74123
        # Create vertex coordinates for each grid cell
        x, y = np.meshgrid(np.array(dd['lut'][0]), np.array(dd['lut'][1]))
        x, y = x.flatten(), y.flatten()
        dosegridpoints = np.vstack((x, y)).T

        maxdose = int(dd['dosemax'] * dd['dosegridscaling'] * 100)
        # Remove values above the limit (cGy) if specified
        if isinstance(limit, int):
            if (limit < maxdose):
                maxdose = limit
        hist = np.zeros(maxdose)
    else:
        return np.array([0])

    n = 0
    planedata = {}
    # Iterate over each plane in the structure
    for z, plane in iteritems(planes):
        # Get the dose plane for the current structure plane
        doseplane = dose.GetDoseGrid(z)
        planedata[z] = calculate_plane_histogram(
            plane, doseplane, dosegridpoints,
            maxdose, dd, id, structure, hist)
        n += 1
        if callback:
            callback(n, len(planes))
    # Volume units are given in cm^3
    volume = sum([p[1] for p in planedata.values()]) / 1000
    # Rescale the histogram to reflect the total volume
    hist = sum([p[0] for p in planedata.values()])
    hist = hist * volume / sum(hist)
    # Remove the bins above the max dose for the structure
    hist = np.trim_zeros(hist, trim='b')

    return hist
    


def calculate_plane_histogram(plane, doseplane, dosegridpoints,
                              maxdose, dd, id, structure, hist):
    """Calculate the DVH for the given plane in the structure."""
    contours = [[x[0:2] for x in c['data']] for c in plane]

    # If there is no dose for the current plane, go to the next plane
    if not len(doseplane):
        return (np.arange(0, maxdose), 0)

    # Create a zero valued bool grid
    grid = np.zeros((dd['rows'], dd['columns']), dtype=np.uint8)

    # Calculate the histogram for each contour in the plane
    # and boolean xor to remove holes
    for i, contour in enumerate(contours):
        m = get_contour_mask(dd, id, dosegridpoints, contour)
        grid = np.logical_xor(m.astype(np.uint8), grid).astype(np.bool)

    hist, vol = calculate_contour_dvh(
        grid, doseplane, maxdose, dd, id, structure)
    return (hist, vol)


def get_contour_mask(dd, id, dosegridpoints, contour):
    """Get the mask for the contour with respect to the dose plane."""
    doselut = dd['lut']

    c = matplotlib.path.Path(list(contour))
    grid = c.contains_points(dosegridpoints)
    grid = grid.reshape((len(doselut[1]), len(doselut[0])))

    return grid


def calculate_contour_dvh(mask, doseplane, maxdose, dd, id, structure):
    """Calculate the differential DVH for the given contour and dose plane."""
    # Multiply the structure mask by the dose plane to get the dose mask
    mask = ma.array(doseplane * dd['dosegridscaling'] * 100, mask=~mask)
    # Calculate the differential dvh
    hist, edges = np.histogram(mask.compressed(),
                               bins=maxdose,
                               range=(0, maxdose))

    # Calculate the volume for the contour for the given dose plane
    vol = sum(hist) * ((id['pixelspacing'][0]) *
                       (id['pixelspacing'][1]) *
                       (structure['thickness']))
    return hist, vol

# ========================== Test DVH Calculation =========================== #


    # Read the example RT structure and RT dose files
    # The testdata was downloaded from the dicompyler website as testdata.zip

    # Obtain the structures and DVHs from the DICOM data

class initialfunction:
    def __init__(self, window):
            self.window = window
            self.window.title("Input Parameters")
            self.window.iconbitmap("C:/Users/Owner/Documents/Rlogo2.ico")
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
            self.label14 = Label(window, text="ROI (exact name from TPS, in quotations)")
            self.label15 = Label(window)
            self.label16 = Label(window)
            self.label17 = Label(window)
            self.label18 = Label(window)
            self.label19 = Label(window)
            self.label20 = Label(window)
            self.label21 = Label(window)
            self.label22 = Label(window)
            self.label23 = Label(window, text = "Quantity of DICOM dose files in Plan 1")
            self.label24 = Label(window, text = "Quantity of DICOM dose files in Plan 2")
            self.box1 = Entry(window)
            self.box2 = Entry(window)
            self.box3 = Entry(window)
            answer = StringVar()
            self.box4 = Entry(window, textvariable=answer)
            self.box5 = Entry(window)
            self.box6 = Entry(window)
            self.button1 = Button(window, text="Calculate", command= self.plot)
            self.button2 = ttk.Button(self.label4, text = "Browse for Plan1 RD.dcm #1", command = self.fileDialog1)
            self.button3 = ttk.Button(self.label5, text = "Browse for Plan1 RD.dcm #2", command = self.fileDialog2)
            self.button4 = ttk.Button(self.label6, text = "Browse for Plan1 RD.dcm #3", command = self.fileDialog3)
            self.button5 = ttk.Button(self.label7, text = "Browse for Plan1 RD.dcm #4", command = self.fileDialog4)
            self.button6 = ttk.Button(self.label8, text = "Browse for struture file RS.dcm" , command = self.fileDialog5)
            self.button7 = ttk.Button(self.label15,text = "Browse for Plan2 RD.dcm #1", command = self.fileDialog6)
            self.button8 = ttk.Button(self.label16,text = "Browse for Plan2 RD.dcm #2", command = self.fileDialog7)
            self.button9 = ttk.Button(self.label17,text = "Browse for Plan2 RD.dcm #3", command = self.fileDialog8)
            self.button10 = ttk.Button(self.label18,text = "Browse for Plan2 RD.dcm #4", command = self.fileDialog9)
            self.button11 = ttk.Button(self.label19,text = "Plan 1")
            self.button12 = ttk.Button(self.label20,text = "Plan 2")
            self.button13 = ttk.Button(self.label21,text = "Plan 1")
            self.button14 = ttk.Button(self.label22,text = "Plan 2")

            self.label1.grid(row=0, sticky=E)
            self.label2.grid(row=1,sticky=E)
            self.label3.grid(row=2,sticky=E)
            self.label14.grid(row=3,sticky=E)
            self.label23.grid(row=4,sticky=E) #quantity of dose files 
            self.label24.grid(row=5,sticky=E)  
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
             
            self.box1.grid(row=0, column=1)
            self.box2.grid(row=1, column=1)
            self.box3.grid(row=2, column=1)
            self.box4.grid(row=3, column=1)
            self.box5.grid(row=4, column=1)
            self.box6.grid(row=5, column=1)

            self.button1.grid(row=18, column=1) #calculate button
            self.button2.grid(row=6, column=1) #choose dose file
            self.button3.grid(row=7, column=1) #choose dose file
            self.button4.grid(row=8, column=1) #choose dose file
            self.button5.grid(row=9, column=1) #choose dose file
            self.button6.grid(row=16, column=1) #choose struct file
            self.button7.grid(row=11, column=2)
            self.button8.grid(row=12, column=1)
            self.button9.grid(row=13, column=1)
            self.button10.grid(row=14, column=1)
            #self.button11.grid(row=15, column=1)
            #self.button12.grid(row=16, column=1)
            #self.button13.grid(row=17, column=1)
            #self.button14.grid(row=18, column=1)
            
    def fileDialog1(self):
        self.filename1 = filedialog.askopenfilename(initialdir="/", title = "Select A File", filetype = (("dicom", "*.dcm"), ("All Files","*.*")))
        self.label4 = ttk.Label(self.label4, text = "")
        self.label4.grid(row=6, sticky=E)
        self.label4.configure(text= self.filename1)
    def fileDialog2(self):
        plan1files =float(self.box5.get())
        if plan1files >= 2:
            self.filename2 = filedialog.askopenfilename(initialdir="/", title = "Select A File", filetype = (("dicom", "*.dcm"), ("All Files","*.*")))
            self.label5 = ttk.Label(self.label5, text = "")
            self.label5.grid(row=7, sticky=E)
            self.label5.configure(text= self.filename2)
        else:
            print("no dose file 2")
    def fileDialog3(self):
        plan1files = float(self.box5.get())
        if plan1files >= 3:
            self.filename3 = filedialog.askopenfilename(initialdir="/", title = "Select A File", filetype = (("dicom", "*.dcm"), ("All Files","*.*")))
            self.label6 = ttk.Label(self.label6, text = "")
            self.label6.grid(row=8, sticky=E)
            self.label6.configure(text= self.filename3)
        else:   
            print("no dose file 3")
    def fileDialog4(self):
        plan1files = float(self.box5.get())
        if plan1files >= 4:
            self.filename4 = filedialog.askopenfilename(initialdir="/", title = "Select A File", filetype = (("dicom", "*.dcm"), ("All Files","*.*")))
            self.label7 = ttk.Label(self.label7, text = "")
            self.label7.grid(row=9, sticky=E)
            self.label7.configure(text= self.filename4)
        else:
            print("no dose file 4")
            
    def fileDialog5(self): #structure file
        self.filename5 = filedialog.askopenfilename(initialdir="/", title = "Select A File", filetype = (("dicom", "*.dcm"), ("All Files","*.*")))
        self.label8 = ttk.Label(self.label8, text = "")
        self.label8.grid(row=16, sticky=E)
        self.label8.configure(text= self.filename5)

    def fileDialog6(self):
        self.filename6 = filedialog.askopenfilename(initialdir="/", title = "Select A File", filetype = (("dicom", "*.dcm"), ("All Files","*.*")))
        self.label15 = ttk.Label(self.label15, text = "")
        self.label15.grid(row=17, sticky=E)
        self.label15.configure(text= self.filename6)

    def fileDialog7(self):
        plan2files =float(self.box6.get())
        if plan2files >= 2:
            self.filename7 = filedialog.askopenfilename(initialdir="/", title = "Select A File", filetype = (("dicom", "*.dcm"), ("All Files","*.*")))
            self.label16 = ttk.Label(self.label16, text = "")
            self.label16.grid(row=18, sticky=E)
            self.label16.configure(text= self.filename7)
        else:
            print("no dose file 2")

    def fileDialog8(self):
        plan2files = float(self.box6.get())
        if plan2files >= 3:
            self.filename8 = filedialog.askopenfilename(initialdir="/", title = "Select A File", filetype = (("dicom", "*.dcm"), ("All Files","*.*")))
            self.label17 = ttk.Label(self.label17, text = "")
            self.label17.grid(row=19, sticky=E)
            self.label17.configure(text= self.filename8)
        else:
            print("no dose file 3")

    def fileDialog9(self):
        plan2files = float(self.box6.get())
        if plan2files >= 4:
            self.filename9 = filedialog.askopenfilename(initialdir="/", title = "Select A File", filetype = (("dicom", "*.dcm"), ("All Files","*.*")))
            self.label18 = ttk.Label(self.label18, text = "")
            self.label18.grid(row=20, sticky=E)
            self.label18.configure(text= self.filename9)
        else:
            print("no dose file 4")

    def plot(self):
            plan1files = float(self.box5.get())
            plan2files = float(self.box6.get())
            self.newWindow=Toplevel(self.window)
            self.newWindow.title("Recalculated DVH")
            self.newWindow.iconbitmap("C:/Users/Owner/Documents/Rlogo2.ico")
            rtssfile1 = self.filename5
            RTss1 = dicomparser.DicomParser(rtssfile1)
            RTstructures1 = RTss1.GetStructures()

            rtdosefile1 = self.filename1
            if plan1files >=2:
                rtdosefile2 = self.filename2
            if plan1files >=3:
                rtdosefile3 = self.filename3
            if plan1files >=4:
                rtdosefile4 = self.filename4
            
            rtdosefile5 = self.filename5
            if plan2files >=2:
                rtdosefile6 = self.filename6
            if plan2files >=3:
                rtdosefile7 = self.filename7
            if plan2files >=4:
                rtdosefile8 = self.filename8

            dpf1 = float(self.box1.get())  # number of fractions
            dpf2 = float(self.box2.get())
            abratio = float(self.box3.get())     # alpha/beta ratio
            enteredtext = self.box4.get()
            #structure = "SPINAL_CANAL"
            # Generate the calculated DVHs
            calcdvhs1 = {}
            calcdvhs2 = {}
            calcdvhs3 = {}
            calcdvhs4 = {}
            calcdvhs5 = {}
            calcdvhs6 = {}
            calcdvhs7 = {}
            calcdvhs8 = {}

            for key, structure in RTstructures1.items():
                calcdvhs1[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile1, key)
                if (key in calcdvhs1) and (structure['name']== enteredtext) and (len(calcdvhs1[key].counts) and calcdvhs1[key].counts[0]!=0):
                    print(structure['name'],calcdvhs1[key].bins)
            
            if plan1files >=2:
                for key, structure in RTstructures1.items():
                    calcdvhs2[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile2, key)
                    if (key in calcdvhs2) and (structure['name']== enteredtext) and (len(calcdvhs2[key].counts) and calcdvhs2[key].counts[0]!=0):
                        print(structure['name'],calcdvhs2[key].bins)
            if plan1files >=3:
                for key, structure in RTstructures1.items():
                    calcdvhs3[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile3, key)
                    if (key in calcdvhs3) and (structure['name']== enteredtext) and (len(calcdvhs3[key].counts) and calcdvhs3[key].counts[0]!=0):
                        print(structure['name'],calcdvhs3[key].bins)
            if plan1files >=4:
                for key, structure in RTstructures1.items():
                    calcdvhs4[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile4, key)
                    if (key in calcdvhs4) and (structure['name']== enteredtext) and (len(calcdvhs4[key].counts) and calcdvhs4[key].counts[0]!=0):
                        print(structure['name'],calcdvhs4[key].bins)
 
            for key, structure in RTstructures1.items():
                calcdvhs5[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile5, key)
                if (key in calcdvhs5) and (structure['name']== enteredtext) and (len(calcdvhs5[key].counts) and calcdvhs5[key].counts[0]!=0):
                    print(structure['name'],calcdvhs5[key].bins)
            
            if plan2files >=2:
                for key, structure in RTstructures1.items():
                    calcdvhs6[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile6, key)
                    if (key in calcdvhs2) and (structure['name']== enteredtext) and (len(calcdvhs2[key].counts) and calcdvhs2[key].counts[0]!=0):
                        print(structure['name'],calcdvhs2[key].bins)
            if plan2files >=3:
                for key, structure in RTstructures1.items():
                    calcdvhs7[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile7, key)
                    if (key in calcdvhs7) and (structure['name']== enteredtext) and (len(calcdvhs7[key].counts) and calcdvhs7[key].counts[0]!=0):
                        print(structure['name'],calcdvhs7[key].bins)
            if plan2files >=4:
                for key, structure in RTstructures1.items():
                    calcdvhs8[key] = dvhcalc.get_dvh(rtssfile1, rtdosefile8, key)
                    if (key in calcdvhs8) and (structure['name']== enteredtext) and (len(calcdvhs8[key].counts) and calcdvhs8[key].counts[0]!=0):
                        print(structure['name'],calcdvhs8[key].bins)

            x1 = np.array((dpf1 + abratio) / (int(2) + abratio))
            x2 = np.array((dpf2 + abratio) / (int(2) + abratio))
            
            volumedata = calcdvhs1[key].counts* 100/calcdvhs1[key].counts[0]
            dosedata1 = np.array(calcdvhs1[key].bins) * x1
            if plan1files >=2:
                dosedata2 = np.array(calcdvhs2[key].bins) * x1
            if plan1files >=3:
                dosedata3 = np.array(calcdvhs3[key].bins) * x1
            if plan1files >=4:
                dosedata4 = np.array(calcdvhs4[key].bins) * x1
            dosedata5 = np.array(calcdvhs5[key].bins) * x1
            if plan2files >=2:
                dosedata6 = np.array(calcdvhs6[key].bins) * x1
            if plan2files >=3:
                dosedata7 = np.array(calcdvhs7[key].bins) * x1
            if plan2files >=4:
                dosedata8 = np.array(calcdvhs8[key].bins) * x1
            
            EPSILON = sys.float_info.epsilon  # smallest possible difference

            def interpolate(inp, fi):
                i = int(fi)
                f = fi - i
                return (inp[i] if f < EPSILON else
                        inp[i] + f*(inp[i+1]-inp[i]))

            inp1 = dosedata1
            if plan1files >=2:
                inp2 = dosedata2
            if plan1files >=3:
                inp4 = dosedata3
            if plan1files >=4:
                inp5 = dosedata4
            inp3 = volumedata
            inp6 = dosedata5
            if plan2files >=2:
                inp7 = dosedata6
            if plan2files >=3:
                inp8 = dosedata7
            if plan2files >=4:
                inp9 = dosedata8
            new_len = 3000

            delta1 = (len(inp1)-1) / float(new_len-1)
            outp1 = [interpolate(inp1, i*delta1) for i in range(new_len)]
            if plan1files >=2:
                delta2 = (len(inp2)-1) / float(new_len-1)
                outp2 = [interpolate(inp2, i*delta2) for i in range(new_len)]   
            delta3 = (len(inp3)-1) / float(new_len-1)
            outp3 = [interpolate(inp3, i*delta3) for i in range(new_len)] 
            if plan1files >=3:
                delta4 = (len(inp4)-1) / float(new_len-1)
                outp4 = [interpolate(inp4, i*delta4) for i in range(new_len)] 
            if plan1files >=4: 
                delta5 = (len(inp5)-1) / float(new_len-1)
                outp5 = [interpolate(inp5, i*delta5) for i in range(new_len)] 
            delta6 = (len(inp6)-1) / float(new_len-1)
            outp6 = [interpolate(inp6, i*delta6) for i in range(new_len)]
            if plan2files >=2:
                delta7 = (len(inp7)-1) / float(new_len-1)
                outp7 = [interpolate(inp7, i*delta7) for i in range(new_len)]             
            if plan2files >=3:
                delta8 = (len(inp8)-1) / float(new_len-1)
                outp8 = [interpolate(inp8, i*delta8) for i in range(new_len)] 
            if plan2files >=4: 
                delta9 = (len(inp9)-1) / float(new_len-1)
                outp9 = [interpolate(inp9, i*delta9) for i in range(new_len)] 
            
            if plan1files ==1:
                interxvaluesplan1 = outp1
            elif plan1files ==2:
                interxvaluesplan1 = np.add(outp1,outp2)
            elif plan1files ==3:
                interxvalues1plan1 = np.add(outp1,outp2)
                interxvaluesplan1 = np.add(interxvalues1plan1, outp4)
            elif plan1files ==4:
                interxvalues1plan1 = np.add(outp1 , outp2)
                interxvalues2plan1 = np.add(outp4, outp5) 
                interxvaluesplan1 = np.add(interxvalues1plan1, interxvalues2plan1)
            
            if plan2files ==1:
                interxvaluesplan2 = outp6
            elif plan2files ==2:
                interxvaluesplan2 = np.add(outp6,outp7)
            elif plan2files ==3:
                interxvalues1plan2 = np.add(outp6,outp7)
                interxvaluesplan2 = np.add(interxvalues1plan2, outp8)
            elif plan2files ==4:
                interxvalues1plan2 = np.add(outp6 , outp7)
                interxvalues2plan2 = np.add(outp8, outp9) 
                interxvaluesplan2 = np.add(interxvalues1plan2, interxvalues2plan2)

            if plan1files==1 and plan2files ==1:
                interxvalues = np.add(outp1, outp6)
            elif plan1files==2 and plan2files ==2:
                interxvalues = np.add(interxvaluesplan1, interxvaluesplan2)
            elif plan1files==3 and plan2files ==3:
                interxvalues = np.add(interxvaluesplan1, interxvaluesplan2)
            elif plan1files==4 and plan2files==4:
                interxvalues = np.add(interxvaluesplan1,interxvaluesplan2)

            fig = Figure()
            ax = fig.add_subplot(111)
            #ax.plot(outp1, outp3, c='m')
            #ax.plot(outp2, outp3, c='b')
            ax.plot(interxvalues, outp3, c='y')
            ax.legend(["Plan 1+2 EQD2"])
            ax.set_ylabel("Volume %", fontsize=14)
            ax.set_xlabel("Dose Gy", fontsize=14)
            ax.set_axisbelow(True)
            datacursor()
            ax.yaxis.grid(color='gray', linestyle='dashed')
            ax.xaxis.grid(color='gray', linestyle='dashed')
            canvas = FigureCanvasTkAgg(fig, master=self.newWindow)
            canvas.get_tk_widget().grid(row=10)
            canvas.draw()
            plt.show()

            toolbarFrame = Frame(master=self.newWindow)
            toolbarFrame.grid(row=20)
            toolbar = NavigationToolbar2Tk(canvas, toolbarFrame)
            toolbar.draw()

window = Tk()
start = initialfunction(window)
window.mainloop()

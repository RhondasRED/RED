# RED

A method to bridge the gap between conventional radiotherapy treatment planning systems (TPS) based on standard fractionation (2 Gy per fraction) and the radiobiological effects arising from non-standard fractionation, for further treatment with anatomical overlap (re-treatment). RE-calculate DVH (RED) is a simple software for the addition of two radiotherapy plans for a common irradiated structure. Equivalent Dose in 2 Gy fractions (EQD2) is used as the biological recalculation method. 
Required input includes dose per fraction, α/β for specific tissue types and DICOM-RT files from the TPS. 
The dose distribution matrix is converted into an EQD2 dose matrix and plotted against structure volume data to create a summed EQD2 DVH.

Requirements:
dicompylercore,
numpy,
matplotlib,
mpldatacursor,
tkinter



dicompylercore is Copyright of (c) 2011-2016 Aditya Panchal: "dicompyler-core" See the file license.txt available at https://github.com/dicompyler/dicompyler-core/

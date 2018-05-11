# gui3.py
# Kenneth Lipke
# Spring 2018

"""
Gui Version 2.0 -- refactoring and cleaning up of the code
"""

import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory, asksaveasfilename
from tkinter import messagebox

import pandas as pd

# # My helper classes 
from Requirement import *
# # from Popup import *
from MenuBar import *
from Optimizer import *
from StudentMetadata import *

# # Helper functions
import clean_data


class MainApp(tk.Frame):
	"""
	Fill in later
	"""

	def __init__(self, parent, *args, **kwargs):
		b = tk.Button(parent, text="Button Test", command=self.test)
		b.pack()


	def test(self):
		print("button pressed")





if __name__ == "__main__":
	root = tk.Tk()
	root.title("Schedule Optimizer")
	root["bg"] = "grey96"
	root.geometry("800x800")
	MainApp(root)
	root.mainloop()


	# print("Starting")
	# root = tk.Tk()
	# print("Root created")
	# root.wm_title("Schedule Optimizer")
	# print("Title assigned")
	# root["bg"] = "grey96"
	# root.geometry("800x800") # fiddle with this, see if you can make it adaptive
	# print("Starting main app")
	# MainApplication(root)
	# root.mainloop()
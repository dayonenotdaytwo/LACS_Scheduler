# Kenneth Lipke
# March 2018
# MenuBar.py

"""
Class for a menubar for the main app
"""

import tkinter as tk
from tkinter import messagebox

from Popup import *

class MenuBar():
	"""
	Buids off of tkinter's Menu widget

	Main Fields
	-----------


	Main Methods
	------------


	"""

	def __init__(self, parent):
		"""
		must be given a main argument, this of class MainApllication


		outline structure of the menubar
		"""

		# Create the basic menu
		self.menu = tk.Menu(parent.master)
		self.parent = parent

		#-----------------------------------------------------------------------
		#                               File Menu
		#-----------------------------------------------------------------------
		# Create file menu
		self.file = tk.Menu(self.menu)

		# add commands
		self.file.add_command(label="Open", command=self.open)
		self.file.add_command(label="Save", command = self.save)
		self.file.add_separator()
		self.file.add_command(label="Quit", command = self.file_quit)
		

		# tie to menubar
		self.menu.add_cascade(label="File", menu=self.file)


		#-----------------------------------------------------------------------
		#                               Help Menu
		#-----------------------------------------------------------------------
		self.menu.add_command(label="Help", command = self.help)



	def file_quit(self):
		"""
		Quits the application, fist asking if you have made sure to save
		"""
		s = "Do you want to quit?\n(Anything not saved will be lost)"
		if messagebox.askokcancel("Quit", s):
			self.parent.master.destroy()

	def open(self):
		"""
		Opens and loads a saved configuration
		"""
		print("Figure out how to do this")

	def save(self):
		"""
		Saves the current configuration
		"""
		print("Figure out how to do this")


	def help(self):
		"""
		Creates a popup window with all relevant help info
		"""
		Popup("We don't know how this works either", "help")


			
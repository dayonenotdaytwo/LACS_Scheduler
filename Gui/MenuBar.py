# Kenneth Lipke
# March 2018
# MenuBar.py

"""
Class for a menubar for the main app
"""

import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askdirectory, asksaveasfilename

from Popup import *
from SavedConfig import *

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
		messagebox.showinfo("Information", 
			"Your saved configuration will have extension .pkl")
		file_name = askopenfilename()

		# open the file
		with open(file_name, "rb") as input:
			s = pickle.load(input)


		self.parent.initial_file_df = s.initial_file_df
		self.parent.courses = s.courses
		self.parent.course_list_selected = s.course_list_selected
		self.parent.LP_input = s.LP_input
		self.parent.teacher_df = s.teacher_df
		self.parent.preference_input_df = s.preference_input_df
		self.parent.prox = s.prox
		self.parent.requirements = s.requirements
		self.parent.hs_preference_df = s.hs_preference_df
		self.parent.ms_preference_df = s.ms_preference_df
		self.parent.rr_df = s.rr_df
		self.parent.student_dict = s.student_dict
		self.parent.need_course_num_dict = s.need_course_num_dict

		if s.requirements is not None:
			# Check if there were any requirements
			# If so, open them, make full versions
			# add them to the list
			for r in s.requirements:
				full_req = r.create_full()
				full_req.create_label(self.parent.req_frame_lower)
				self.parent.requirements.append(full_req)



	def save(self):
		"""
		Saves the current configuration
		"""
		# get file path
		messagebox.showinfo("Information","When saving do not put file extension")
		file_name = asksaveasfilename()


		s = SavedConfig(
				initial_file_df = self.parent.initial_file_df,
				courses = self.parent.courses,
				course_list_selected = self.parent.course_list_selected,
				LP_input = self.parent.LP_input,
				teacher_df = self.parent.teacher_df,
				preference_input_df = self.parent.preference_input_df,
				prox = self.parent.prox,
				requirements = self.parent.requirements,
				hs_preference_df = self.parent.hs_preference_df,
				ms_preference_df = self.parent.ms_preference_df,
				rr_df = self.parent.rr_df,
				student_dict = self.parent.student_dict,
				need_course_num_dict = self.parent.need_course_num_dict)
		s.save(file_name)
		print("Save successful")






	def help(self):
		"""
		Creates a popup window with all relevant help info
		"""
		Popup("We don't know how this works either", "help")


			
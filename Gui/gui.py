# Kenneth Lipke
# March 27, 2018
# gui.py

"""
Master GUI class for schedule optimizer
"""

import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory

# My helper classes 
from Requirement import *
from Popup import *

import pandas as pd

class MainApplication(tk.Frame):
	"""
	Main application for the user interface, allows the user to select the
	required files to make the schedule, as well as creating the intermediate
	sheets for them to use

	Key Attributes
	--------------


	Key Methods
	-----------


	"""
	def __init__(self, parent, *args, **kwargs):
		"""
		Creates the first, and main, window for the application
		This window contains a file selection frame
		then a requirement frame which allows a user to add, remove, and 
		keep track of requirements

		Parameters
		----------
		parent - the main root for the application (should be created in main)

		*args, **kwargs - arguments for the main window (can't see these being
							needed)
		"""

		"""
		What files do we need the school to fill out / select:
		1) Initial file that lists all courses, as well as if they are multi-instance
			if they are double periods, the subject, max/min capacities

		2) Secondary file listing the teachers for each of the courses

		3) Student Preference Document (the form response)
		"""

		# Document Upload Fields 
		self.initial_file = None
		self.secondary_file = None
		self.preference_file = None
		self.completed_preference_file = None

		# Derivate information fields
		self.courses = None # list of courses
		self.course_list_selected = False # initialize for popup

		# user created
		self.requirements = [] # empty list


		# test directory save
		#tk.Button(parent, text="test directory", command = askdirectory).pack()
		#dir_name = tk.askdirectory()


		#----------------------------------------------------------
		#					File Selection Frame
		#----------------------------------------------------------
		"""
		Grid layout (5x3)
		label prompt & select button & label displaying the file name
		"""
		# Create the frame
		self.file_select_frame = tk.Frame(parent, bd=10, bg="grey84")
		self.file_select_frame.pack(pady=10)

		# First file
		s = "Step 1: Please select the file list all courses:"
		tk.Label(self.file_select_frame, text=s).grid(row=1, column = 1,
			stick="W")
		tk.Button(self.file_select_frame, text="Select",
			command=self.get_initial_file).grid(row=1, column=2)

		# Button to create second file for them to fill out
		s = "Step 2: Create file to fill in teachers"
		s += "\n(select where it should be saved): "
		tk.Label(self.file_select_frame, text=s).grid(row=2, column=1,
			sticky="W")
		tk.Button(self.file_select_frame, text="Make File", 
			command = self.make_teacher_file).grid(row=2, column=2)


		# Second file
		s = "Step 3: Select file with teacher mapping: "
		tk.Label(self.file_select_frame, text=s).grid(row=3, column=1,
			sticky="W")
		tk.Button(self.file_select_frame, text="Select", 
			command=self.get_secondary_file).grid(row=3, column=2)

		# Make spreadsheet for student preferenfes, and LP input
		s = "Step 4: Generate preference form: "
		s += "\n(select where it should be saved):"
		tk.Label(self.file_select_frame, text=s).grid(row=4, column=1, 
			sticky="W")
		tk.Button(self.file_select_frame, text="Make File",
			command=self.make_preference_form).grid(row=4, column=2)

		# Upload student preferences
		s = "Step 5: Upload student preferences:"
		tk.Label(self.file_select_frame, text=s).grid(row=5, column=1,
			sticky="W")
		tk.Button(self.file_select_frame, text="Select", 
			command=self.get_preference_file).grid(row=5, column=2)



		#----------------------------------------------------------
		#					Add RequirementFrame
		#----------------------------------------------------------
		self.requirements = [] # list containing requirement classes
		self.req_frame = tk.Frame(parent)
		self.req_frame.pack(pady=10)

		# Upper frame (contains buttons)
		self.req_frame_upper = tk.Frame(self.req_frame, bg="LightBlue1")
		self.req_frame_upper.pack()

		# Button to add req
		self.add = tk.Button(self.req_frame_upper, text="Add Requirement",
			command = self.add_req)
		#self.add.pack(side='left', padx=10)
		self.add.grid(row=1, column=1)

		# Add button to delete requirement
		self.delete = tk.Button(self.req_frame_upper, text="Remove Requirement",
			command = self.del_req)
		#self.delete.pack(side='right', padx=10)
		self.delete.grid(row=1, column=2)

		# Add label saying what to do
		s = "Add Requirements: Once Step 1 is completed, and a document containing"
		s += "\n a column `Course Name` is found, you can add grade level requirements"
		#tk.Label(self.req_frame_upper, text=s).pack(side="bottom")
		tk.Label(self.req_frame_upper, text=s).grid(row=0, column=1, columnspan=2)

		# Lower frame, contains the requirements (uppded when added)
		self.req_frame_lower = tk.Frame(self.req_frame)
		self.req_frame_lower.pack()


		#----------------------------------------------------------
		#					Optimization Frame
		#----------------------------------------------------------
		"""
		Button to save the current configuration
		Button to load a previously saved configuration
		Slider to set optimizaiton speed (inverse MIPGap)
		Button to start optimization
		"""


		#----------------------------------------------------------
		#					Results Frame
		#----------------------------------------------------------

	def get_initial_file(self):
		"""
		Saves down the intial file from the first button
		"""
		# save the file name
		self.initial_file = askopenfilename()
		df = pd.read_csv(self.initial_file)

		# make sure it has the right column header
		if "Course Name" not in df.columns:
			Popup("Make sure this file has a column 'Course Name'")
			return 

		# get the course list
		self.courses = df["Course Name"]
		self.course_list_selected = True

		# Create a label for the UI
		tk.Label(self.file_select_frame,
			text = "  " + self.get_file_name(self.initial_file)
			).grid(row=1, column=3)


	def get_file_name(self, file):
		"""
		Returns the name of the file after the last /
		"""
		return file[file.rfind("/") + 1:]

	def make_teacher_file(self):

		print("Complete with Justina's script")
		dir_name = askdirectory()
		print(dir_name)


	def get_secondary_file(self):
		"""
		gets the teacher file
		"""
		# get the file
		self.secondary_file = askopenfilename()

		# make the label
		tk.Label(self.file_select_frame,
			text = "  " + self.get_file_name(self.secondary_file)).grid(
			row = 3, column=3, sticky="W")

		print("TODO: add justina's script for making final LP input with this")

	def make_preference_form(self):
		print("Add Dae Won's script to generate form")

	def get_preference_file(self):
		"""
		Selects the file for the filled out student preferences,
		then run's the scipt to turn them into useable LP inputs
		"""
		self.completed_preference_file = askopenfilename()
		tk.Label(self.file_select_frame, 
			text = " " + self.get_file_name(self.completed_preference_file)
			).grid(row=5, column=3, sticky="W")

		print("Run Justina's script to make LP input preferences")


	def add_req(self):
		"""
		Adds requirements, creates a popup window with the prompts to add
		requirements, pulls course list from a selected file
		-----> COME BACK AND SPECIFY WHICH FILE <---------
		"""
		# Create new window
		print(self.courses)
		if self.course_list_selected == False:
			Popup("Must Select Course File First")
			#self.popup("Must Select Course File First")
			return 

		pop = tk.Toplevel()
		f = tk.Frame(pop)
		f.pack()

		# Label
		l1 = tk.Label(f, text="Students in Grade", justify='left')
		l1.pack(side='left')

		# Grade Select
		grade_options = [5,6,7,8,9,10,11,12]
		grade = tk.IntVar(pop)
		grade.set(5)
		grade_menu = tk.OptionMenu(f, grade, *tuple(grade_options))
		grade_menu.pack(side='left')

		# Middle Label
		l2 = tk.Label(f, text="Must take", justify='left')
		l2.pack(side='left')

		# Course select
		Courses = ["Math", "Science", "English"]
		course1 = tk.StringVar(f)
		course1.set("None")
		# choose1 = tk.OptionMenu(f, course1, *tuple(Courses))
		choose1 = tk.OptionMenu(f, course1, *tuple(list(self.courses)))
		choose1.pack(side='left')

		# OR label
		l3 = tk.Label(f, text="OR (leave blank if no or condition)", justify='left')
		l3.pack(side='left')

		# Course select 2
		course2 = tk.StringVar(f)
		course2.set("None")
		# choose2 = tk.OptionMenu(f, course2, *tuple(Courses))
		choose2 = tk.OptionMenu(f, course2, *tuple(list(self.courses)))
		choose2.pack(side='left')

		# Button to add
		def finished():
			"""
			(innter function)
			creates a new requirement instance, adds a label to main window
			then kills the popup window
			"""
			if course2.get() == "None":
				r = Requirement(grade.get(), course1.get())
			else:
				r = Requirement(grade.get(), course1.get(), course2.get())
			
			# add the new requirement
			self.requirements.append(r) 

			# display the new requirement 
			r.create_label(self.req_frame_lower)

			# kill this window
			pop.destroy()


		add_but = tk.Button(f, text="Add", command = finished)
		add_but.pack(side='bottom', padx=10, pady=10)


	def del_req(self):
		"""
		Creates a popup window that lists all the current requirements
		and lets you select one to delete
		"""
		pop = tk.Toplevel()
		f = tk.Frame(pop)
		f.pack()

		# Add checkboxes for all 
		del_dict = {}
		for r in self.requirements:
			del_dict[r] = tk.IntVar()
			del_dict[r].set(0)
			tk.Checkbutton(f, text=r.describe(), variable=del_dict[r]).pack()

		def done():
			"""
			(inner function)
			Deletes the requirements with checks, then closes the window
			"""
			for r in del_dict:
				if del_dict[r].get() == 1:
					# delete the labels:
					r.remove_label()
					self.requirements.remove(r)

			# closes the window when finished
			pop.destroy()

		# Finished button
		tk.Button(pop, text="Finished", 
			command = done).pack(side='bottom', pady=10)



###
# Eventually move this to its own main script
###

if __name__ == "__main__":
    root = tk.Tk()
    root.wm_title("Schedule Optimizer")
    root.geometry("400x400") # fiddle with this, see if you can make it adaptive
    MainApplication(root)
    root.mainloop()
import tkinter as tk
from tkinter.filedialog import askopenfilename

import pandas as pd

class MainApplication(tk.Frame):
	def __init__(self, parent, *args, **kwargs):
		# self.frame = tk.Frame.__init__(self, parent, *args, **kwargs)

		#----------------------------------------------------------
		#					File Selection Frame
		#----------------------------------------------------------
		# Put the Select Button
		self.file_select_frame = tk.Frame(parent)
		self.file_select_frame.pack()
		self.file = None # initilaize file
		self.select_button = tk.Button(self.file_select_frame, 
			text="Select File",
			command = self.get_file_name)
		self.select_button.pack(side='left')

		# Put the file name
		self.file_label = tk.Label(self.file_select_frame, 
			text="None")
		self.file_label.pack(side='left')

		self.open_button = tk.Button(self.file_select_frame ,
			text="Open", command = self.open_file)
		self.open_button.pack(side='left', padx=1)


		#----------------------------------------------------------
		#					Add RequirementFrame
		#----------------------------------------------------------
		self.requirements = [] # list containing requirement classes
		self.req_frame = tk.Frame(parent, highlightbackground="red")
		self.req_frame.pack(pady=10)

		self.req_frame_upper = tk.Frame(self.req_frame)
		self.req_frame_upper.pack()

		# Button to add req
		self.add = tk.Button(self.req_frame_upper, text="Add Requirement",
			command = self.add_req)
		self.add.pack(side='left', padx=10)

		# Add button to delete requirement
		self.delete = tk.Button(self.req_frame_upper, text="Remove Requirement",
			command = self.del_req)
		self.delete.pack(side='right', padx=10)

		self.req_frame_lower = tk.Frame(self.req_frame)
		self.req_frame_lower.pack()




	def get_file_name(self):
		filename = askopenfilename()
		print(filename)

		# save the filename
		self.file = filename

		# update the label
		filename = filename[filename.rfind("/")+1:]
		self.file_label.config(text=filename)

	def open_file(self):
		if self.file != None:
			df = pd.read_csv(self.file)
			print(df)
		else:
			popup("Need to select a file first")

	def hi(self):
		print("Hi")


	def popup(self, message, title="Warning"):
		win = tk.Toplevel()
		win.wm_title(title)

		l = tk.Label(win, text=message)
		l.pack()

		b = tk.Button(win, text="Okay", command=win.destroy)
		b.pack()

	def add_req(self):
		# Create new window
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
		choose1 = tk.OptionMenu(f, course1, *tuple(Courses))
		choose1.pack(side='left')

		# OR label
		l3 = tk.Label(f, text="OR (leave blank if no or condition)", justify='left')
		l3.pack(side='left')

		# Course select 2
		course2 = tk.StringVar(f)
		course2.set("None")
		choose2 = tk.OptionMenu(f, course2, *tuple(Courses))
		choose2.pack(side='left')

		# Button to add
		def finished():
			if course2.get() == "None":
				r = Requirement(grade.get(), course1.get())
			else:
				r = Requirement(grade.get(), course1.get(), course2.get())
			
			# add the new requirement
			self.requirements.append(r) 

			# display the new requirement 
			# l = r.create_label(self.req_frame)
			# l.pack()
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
			Deletes the requirements with checks, then closes the window
			"""
			for r in del_dict:
				if del_dict[r].get() == 1:
					# delete the labels:
					r.remove_label()
					self.requirements.remove(r)

			pop.destroy()

		# Finished button
		tk.Button(pop, text="Finished", 
			command = done).pack(side='bottom', pady=10)




class Requirement():
	"""
	Class that reprseents a requirement, containts grade, and the one or two classes
	that must be taken by students in this grade
	"""

	def __init__(self, grade, course1, course2=None):
		self.grade = grade
		self.course1 = course1
		self.course2 = course2
		self.labels = [] # list of all labels for this requirement

	def create_label(self, parent, **args):
		"""
		Creates a tkinter Label attached to the parent widget
		that describes the requirement in text
		"""
		s = "Students in grade " + str(self.grade) + " must take " + \
			str(self.course1)
		if self.course2 != None:
			s += " or " + self.course2

		l = tk.Label(parent, text=s, justify = 'left')
		l.pack(**args)

		self.labels.append(l)

		#return self.label

	def remove_label(self):
		"""
		Removes the label from wherever it was put
		"""
		for l in self.labels:
			l.destroy()

	def describe(self):
		"""
		Returns string description
		"""
		s = "Students in grade " + str(self.grade) + " must take " + \
			str(self.course1)
		if self.course2 != None:
			s += " or " + self.course2
		return s






if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x400")
    # MainApplication(root).pack(side="top", fill="both", expand=True)
    MainApplication(root)
    root.mainloop()
# Kenneth Lipke
# 3/27/2018
# Requirement.py

"""
Containts Requirement class, which stores grade level requirements
"""

import tkinter as tk

class Requirement():
	"""
	Class that reprseents a requirement, containts grade, and the one or two classes
	that must be taken by students in this grade

	"""

	def __init__(self, grade, course1, course2=None):
		"""
		Parameters 
		----------
		grade - grade leve (int) that requirement applies to

		course1 - the course name (string) that student must take

		course2 - the second 'OR' course the students must take
					 (None if not included)
		"""

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
		Removes the label (all labels) from wherever it was put
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



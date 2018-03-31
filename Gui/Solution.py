# Solution.py
# Kenneth Lipke
# Spring 2018

"""
File containing the Solution class
This has all the variables and a dictionary to their value
it also has the required data to make sense of these, i.e.,
the student list, the course list, the teacher list, and the room list.
Methods to construct master schedules, and student schedules,
as well as relevant statistics are included
"""

import numpy as np
import pandas as pd

class Solution():
	"""
	Put Full description here

	Key Fields
	----------


	Key Methods
	-----------


	"""

	def __init__(self, courses, rooms, teachers, students,
			x_var_dict, c_var_dict, r_var_dict,
			u_var_dict):
		"""

		Parameters
		----------
		courses	 	- dictinoary of course to their number (Cd)

		rooms 		- list of all rooms

		teachers 	- matrix of courses and teachers, indicating who teachers

		students	- list of all students

		x_var_dict	- the dictionary mapping (studnt, course) to value

		c_var_dict 	-  dictionary mapping (course, period) to value

		r_var_dict 	- dictinoary mapping (course, room, time) to value

		u_var_dict	- dictionary mapping (student, course, period) to value

		"""

		# set inputs
		self.m = model
		self.Cd = courses
		self.R = rooms
		self.Ta = teachers
		self.S = students
		self.XV = x_var_dict
		self.CourseV = c_var_dict
		self.RV = r_var_dict
		self.UV = u_var_dict

		# Get values in dictinary
		# first get list of courses that are not other:
		self.c_mini = []
		for j in self.Cd:
			if "Other" not in self.Cd[j] and "Empty" not in self.Cd[j]:
				c_mini.append(j)





		## TODO NEXT:
		# Get all the description functions from forgb2, 
		# copy them over here, and add a few more save methods
		# Then add a results frame to the GUI







		

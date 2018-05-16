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
import pickle

class Solution():
	"""
	Put Full description here

	Key Fields
	----------


	Key Methods
	-----------


	"""

	def __init__(self, Cd, C, XV, CourseV,
			RoomV, student_dict, I_C_dict, Ta, R, m, save_loc):
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
		self.Cd = Cd
		self.C = C
		self.XV = XV
		self.CourseV = CourseV
		self.RoomV = RoomV
		self.student_dict = student_dict
		self.I_C_dict = I_C_dict
		self.Ta = Ta
		self.R = R
		#self.m = m
		self.save_loc = save_loc

		# Get values in dictinary
		# first get list of courses that are not other:
		# self.c_mini = []
		# for j in self.Cd:
		# 	if "Other" not in self.Cd[j] and "Empty" not in self.Cd[j]:
		# 		c_mini.append(j)




	def save(self):
		"""
		Pickles the soltuions and saves it to the save location
		"""
		pickle.dump(self, open(self.save_loc, "wb"), pickle.HIGHEST_PROTOCOL)
		print("Save compelted")






		## TODO NEXT:
		# Get all the description functions from forgb2, 
		# copy them over here, and add a few more save methods
		# Then add a results frame to the GUI

def open_sol(file):
	"""
	takes in the path to a pickled solution file
	returns the solution object
	"""
	S = pickle.load(open(file, "rb"))
	return S





		

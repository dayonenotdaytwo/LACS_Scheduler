# model1.py
# Kenneth Lipke

"""Script for model contained in Schedule-1-11.ipynb, with additions for 
better post model statistics, as well as better structure for model
sensitivity testing"""

from pyscipopt import Model, quicksum
import numpy as np
import pandas as pd

import sys
import os
import tempfile
from contextlib import contextmanager


def read_preference_data(s1, s2, s3):
	"""reads prefrence data from .csv's
	Input: s1, s2, s3 are strings pointing to .csv files for the first, second,
			and third choice binary preferences, respectively
	Output: 3 2-Dimensional arrays containing the binary preferences,
			set of Students, and set of Courses"""

	print("Reading Data")
	Schedule1 = pd.read_csv(s1)
	Schedule2 = pd.read_csv(s2)
	Schedule3 = pd.read_csv(s3)

	# Get set of all courses
	COURSES = {}
	i = 0
	for course in Schedule1.columns[1:]: #1: as we don't want index column
		COURSES[i] = course
		i += 1

	# Get set of all students (ID in first col of data)
	STUDENTS = {}
	i = 0
	for student in Schedule1[Schedule1.columns[0]]:
		STUDENTS[i] = student
		i += 1

	# Verify all columns match
	not_matching = []
	for i in range(len(Schedule1.columns)):
	    if (Schedule1.columns[i] != Schedule2.columns[i] or 
	    		Schedule2.columns[i] != Schedule3.columns[i] or 
	    		Schedule1.columns[i] != Schedule3.columns[i]):
	        not_matching.append(i)
	if len(not_matching) == 0:
	    print("\tColumns Match")
	else:
	    raise ValueError("Columns in data files do not match")

	 # Make Data arrays
	Schedule1_array = np.zeros([Schedule1.shape[0], Schedule1.shape[1]-1])
	for i in range(Schedule1.shape[0]):
	    Schedule1_array[i] = Schedule1.iloc[i,1:].tolist()

	Schedule2_array = np.zeros([Schedule2.shape[0], Schedule2.shape[1]-1])
	for i in range(Schedule2.shape[0]):
	    Schedule2_array[i] = Schedule2.iloc[i,1:].tolist()

	Schedule3_array = np.zeros([Schedule3.shape[0], Schedule3.shape[1]-1])
	for i in range(Schedule3.shape[0]):
	    Schedule3_array[i] = Schedule3.iloc[i,1:].tolist()


	return Schedule1_array, Schedule2_array, Schedule3_array, STUDENTS, COURSES

def read_MAX_data(file_name):
	"""Reads the max class size data from the file at "file_name" and creates
	a dictionary, each entry is the course name, and the value is the max class size"""

	df = pd.read_csv(file_name)
	courses = df['0']
	sizes = df['Size']

	MAX = {}
	for i in range(len(courses)):
		MAX[courses[i]] = sizes[i]

	return MAX

def read_grade_data(file_name, STUDENTS):
	"""Reads .csv file with two columns, the first is the uinque student identifier, the 
	second is the grade of that student, also takes in STUDENTS so we get same ID
	Returns a dictionary of student ID to grade"""

	gdf = pd.read_csv(file_name, header=None)
	key = gdf[gdf.columns[0]] # student ID column
	grades = gdf[gdf.columns[1]] # Grade column
	
	GRADES = {}
	i = 0
	for s in STUDENTS:
	    GRADES[s] = grades[i] # doing this key so that it matches with STUDENTS
	    i += 1

	return GRADES



class ScheduleModel:
	"""Class for our Schedule model

	fields:
	m			pyscipopt Model
	s1			Binary first choice preferences
	s2			Binary second choice preferences
	s3			Binary third choice preferences
	STUDENTS	Dictionary of all students, key is an int, maps to unique ID
	COURSES		Dictionary of all courses, key is an int, maps to course name
	MAX			Dictionary of max course size, key is the course name
	X			Dictionary of model varialbes. There are 3 variables per student
					each binary, representing whether or not that student
					was assigned his or her, first, second, or third choice
	GRADES		Dicionary of unique student ID to that students grade

	methods:

	"""

	def __init__(self, s1, s2, s3, STUDENTS, COURSES, MAX, GRADES):
		"""takes in data (mostly from read_preference_data function), sets fields, and 
		initilaizes the pyscipopt model instance, as well as adds the variables"""


		# Create model instance
		self.m = Model()

		# Assign data
		self.s1 = s1
		self.s2 = s2
		self.s3 = s3
		self.STUDENTS = STUDENTS
		self.COURSES = COURSES
		self.MAX = MAX
		self.GRADES = GRADES

		# Create appopriate number of variables
		self.X = {}
		for i in range(len(self.STUDENTS)):
			for j in [1,2,3]: # representing first, second, or third choice
				name = str(STUDENTS[i]) + " pref " + str(j)
				self.X[i,j] = self.m.addVar(name, vtype='B')


	#TODO Think about how you are going to deal with max sizes for tinkering

	def set_objective(self, weight_list, grade_dict=None):
		"""Takes in a list of weights "weight_list" that is the weights on which schedule
		a student is assigned, e.g. [3,2,1] would award 3 points when a student gets their first
		choice schedule. grade_dict is an optional input, if given, it must have an entry for each
		different grade, i.e. 5 to 12 which maps to a weight. This weight puts a reward on giving
		an individual in that grade their first choice schedule (and weight-1 for their second choice)
		Sets the objective associated with self.m"""

		first = weight_list[0]
		second = weight_list[1]
		third = weight_list[2]

		# Deal with grades
		## I will make another dictionary that maps seniors and 8th graders
		## to 2 pts, while everyone else to 1 points


		if grade_dict == None:
			# make own dictionary basic weights
			## I will make another dictionary that maps seniors and 8th graders
			## to 2 pts, while everyone else to 1 points
			grade_dict = {}
			for s in self.GRADES:
				if self.GRADES[s] == 8 or self.GRADES[s] == 12:
					grade_dict[s] = 2
				elif self.GRADES[s] == 7 or self.GRADES[s] == 11:
					grade_dict[s] = 1
				else:
					grade_dict[s] = 0
		else:
			# a dictionary is provided, verify that it has enough entries
			if len(grade_dict)==8:
				for g in [5,6,7,8,9,10,11,12]:
					if g not in grade_dict:
						raise ValueError("Dictionary does not have correct values")
				print("User specified grade weight dictionary is valid")


		# Add objective to model
		self.m.setObjective(quicksum(first*self.X[s,1] + second*self.X[s,2] + third*self.X[s,3]
						 for s in self.STUDENTS) + 
							quicksum(grade_dict[s]*self.X[s,1] for s in self.STUDENTS), "maximize")

		print("Objective Set")

	def set_assignment_cons(self):
		"""Adds the assignment constaint to the model, i.e. that each student is 
		assigned to exactly one of their choice"""

		for s in range(len(self.STUDENTS)):
			self.m.addCons(self.X[s,1] + self.X[s,2] + self.X[s,3] == 1)

		print("Assignment Constraint Set")


	def set_max_cons(self):
		"""Sets the max class size constraint"""

		for c in range(len(self.COURSES)):
			self.m.addCons(quicksum(self.X[s,1]*self.s1[s,c] + self.X[s,2]*self.s2[s,c]
							 + self.X[s,3]*self.s3[s,c] 
							 for s in range(len(self.STUDENTS))) <= self.MAX[self.COURSES[c]])
		print("Max Size Constraint Set")


	def solve(self):
		"""solve the modeL"""
		print("Solving")
		self.m.hideOutput() # supresses solve log from printing
		self.m.optimize()
		print("Solve Completed")

	def describe_solution(self):
		"""Describe the solution"""
		Results = {}
		first_choices = 0
		second_choices = 0
		third_choices = 0

		# initilize dictionary to keep track of choices by grade
		grade_first_choices = {}
		grade_second_choices = {}
		grade_third_choices = {}

		for i in range(5,13):
			grade_first_choices[i] = 0
			grade_second_choices[i] = 0
			grade_third_choices[i] = 0

		if self.m.getStatus() != "optimal":
			print("The problem is", self.m.getStatus())
		else:
			print("\nFound Optimal Solution:")
			for i in range(len(self.STUDENTS)):
				for j in [1,2,3]:
					v = self.m.getVal(self.X[i,j]) # value of variable (either 1 or 0)
					if v == 1:
						grade = int(self.GRADES[i]) # this students grade
						if j == 1:
							first_choices += 1 # high level tally
							grade_first_choices[grade] = grade_first_choices[grade] + 1 # tally by grade
						elif j == 2:
							second_choices += 1
							grade_second_choices[grade] = grade_second_choices[grade] + 1
						else:
							third_choices += 1
							grade_third_choices[grade] = grade_third_choices[grade] + 1
						Results[self.STUDENTS[i]] = j

						


			print("Assigned", first_choices, "to top choice", second_choices, "to second, and",
				third_choices, "to the third choice")

			print("\nBreakdown by Grade:")
			print("Grade\t\tFirst\tSecond\tThird")
			for grade in grade_first_choices:
				print("-"*40)
				# get choice distribution for given grade
				num_first = grade_first_choices[grade]
				num_second = grade_second_choices[grade]
				num_third = grade_third_choices[grade]
				print(str(grade) + "\t\t" + str(num_first) + "\t" +
					str(num_second) + "\t" + str(num_third))

			




if __name__=="__main__":

	s1, s2, s3, STUDENTS, COURSES = read_preference_data("Resources/FirstChoiceBinary.csv", 
		"Resources/SecondChoiceBinary.csv", "Resources/ThirdChoiceBinary.csv")
	MAX = read_MAX_data("Resources/CourseSize.csv")
	GRADES = read_grade_data("Resources/Grades.csv", STUDENTS)
	#print(COURSES)

	s = ScheduleModel(s1, s2, s3, STUDENTS, COURSES, MAX, GRADES)
	s.set_objective([3,2,1])
	s.set_assignment_cons()
	s.set_max_cons()
	s.solve()
	s.describe_solution()

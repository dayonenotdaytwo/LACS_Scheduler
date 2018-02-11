# model1.py
# Kenneth Lipke

"""Script for model contained in Schedule-1-11.ipynb, with additions for 
better post model statistics, as well as better structure for model
sensitivity testing"""

from pyscipopt import Model, quicksum
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
				for g in [-1, 5,6,7,8,9,10,11,12]:
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

	def describe_solution(self, heatmap_filename="Heatmap_enrollments_test.png", 
		text_file_name="output_test.txt"):
		"""Describe the solution"""
		Results = {}
		first_choices = 0
		second_choices = 0
		third_choices = 0

		# text file to save description output
		f = open(text_file_name, "w")

		# initilize dictionary to keep track of choices by grade
		grade_first_choices = {}
		grade_second_choices = {}
		grade_third_choices = {}

		#for i in range(5,13):
		for i in [-1,5,6,7,8,9,10,11,12]:
			grade_first_choices[i] = 0
			grade_second_choices[i] = 0
			grade_third_choices[i] = 0

		# Verify that solution is optimal
		if self.m.getStatus() != "optimal":
			print("The problem is", self.m.getStatus())
		else:
			# Given that it is optimal, gather the stats
			print("\nFound Optimal Solution:")

			## Determine number of each choice given out
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

			# Print the number of each choice given out
			s = ("Assigned " + str(first_choices) + " to top choice; " + str(second_choices) +
				 " to second; and " + str(third_choices) +  " to the third choice")
			print(s)
			f.write(s) ## write to file

			# Collect a breakdown of first, second, thid choices by grade
			print("\nBreakdown by Grade:")
			f.write("\n\nBreakdown by Grade:")
			print("Grade\t\tFirst\tSecond\tThird")
			f.write("\nGrade\t\tFirst\tSecond\tThird")
			for grade in grade_first_choices:
				print("-"*40)
				f.write("\n"+"-"*40)
				# get choice distribution for given grade
				num_first = grade_first_choices[grade]
				num_second = grade_second_choices[grade]
				num_third = grade_third_choices[grade]
				s = (str(grade) + "\t\t" + str(num_first) + "\t" +
					str(num_second) + "\t" + str(num_third))
				print(s)
				f.write("\n" + s)
			print("-"*40)
			print("\n")
			f.write("\n" + "-"*40 + "\n")

			# Get Course capactities and sizes for output
			# print("\nCourse Capacity:")
			# print("Course" + 34*" " + "Size\tCap")
			# print(55*"-")
			# class_sizes = np.zeros(len(self.COURSES))
			# for j in range(len(self.COURSES)):
			# 	num_enrolled = 0
			# 	for i in range(len(self.STUDENTS)):
			# 		num_enrolled += (self.m.getVal(self.X[i,1])*self.s1[i,j] +
			# 						self.m.getVal(self.X[i,2])*self.s2[i,j] + 
			# 						self.m.getVal(self.X[i,3])*self.s3[i,j])
			# 	name = self.COURSES[j]
			# 	first_space = (40-len(name))*" "
			# 	cap = self.MAX[self.COURSES[j]]
			# 	#print(self.COURSES[j], , num_enrolled, "/", self.MAX[self.COURSES[j]])
			# 	print(name + first_space + str(int(num_enrolled)) + "\t" + str(cap))
			# 	print(55*"-")
			# 	class_sizes[j] = num_enrolled

			## Breakdown courses by number of each grade type enrolled
			print("\nCourse Enrollment by Grade")
			print("Course" + 34*" " + "\t5th\t6th\t7th\t8th\t9th\t10th\t11th\t12th\t|Total\tCapacity")
			print(130*"-")

			# write above
			f.write("\n\nCourse Enrollment by Grade")
			f.write("\nCourse" + 34*" " + "\t5th\t6th\t7th\t8th\t9th\t10th\t11th\t12th\t|Total\tCapacity")
			f.write("\n" + 130*"-")

			# find 6thGradeOther and ignore for the hatmaps
			other_indicies = []
			for i in range(len(self.COURSES)):
				if "6thGradeOther" in self.COURSES[i]:
					other_indicies.append(i)
			num_rows = len(self.COURSES) - len(other_indicies) # for data matrix
			iter_list = list(set(range(len(self.COURSES))) - set(other_indicies))

			# Track data for heat map
			data = np.zeros([len(self.COURSES), 8]) # courses by grade levels
			#data = np.zeros([num_rows, 8]) # courses by grade levels


			for j in range(len(self.COURSES)):
				# intialize grade count dict for each class
				d = {}
				for g in [-1, 5,6,7,8,9,10,11,12]:
					d[g] = 0

				for i in range(len(self.STUDENTS)):
					# check if this student enrolled in this class
					# note, the following is either 1 or 0
					enrolled = (self.m.getVal(self.X[i,1])*self.s1[i,j] +
									self.m.getVal(self.X[i,2])*self.s2[i,j] + 
									self.m.getVal(self.X[i,3])*self.s3[i,j])
					# add to dictionary for correct grade
					d[self.GRADES[i]] += enrolled

					# add to data matrix
					data[j, int(self.GRADES[i]-5)] += enrolled # the -5 so that we translate grades to indicies


				name = self.COURSES[j]
				first_space = (40 - len(name))*" "
				s = name + first_space
				total = 0 # the total number enrolled in the course
				for g in [5,6,7,8,9,10,11,12]:
					s += "\t" + str(int(d[g]))
					total += int(d[g])
				# add total and capacity to the string
				cap = self.MAX[self.COURSES[j]]
				s += "\t|" + str(total) + "\t" + str(cap)
				print(s)
				print(130*"-")
				f.write("\n" + s)
				f.write("\n" + 130*"-")

			# drop the 6th grade rows 
			#print(iter_list)
			data = data[iter_list, :]
			course_labels = np.array(list(self.COURSES.values()))[iter_list]

			f.close() # close the output text file

			# Make heat map of data
			plt.figure(figsize=(12,15)) # height by width
			plt.title("Course Assignments by Grade")
			plt.xlabel("Grade")
			plt.xticks(np.arange(.5,8.5,1), [str(i) + "th" for i in range(5,13)])
			#ylim = len(self.COURSES)
			ylim = len(course_labels)
			#plt.yticks(np.arange(.5,ylim+.5,1), self.COURSES.values(), fontsize=7)
			plt.yticks(np.arange(.5,ylim+.5,1), course_labels, fontsize=7)
			plt.gca().invert_yaxis()
			c = plt.pcolor(data, cmap="plasma", edgecolors="white")
			plt.colorbar(c)
			plt.tight_layout()
			plt.savefig(heatmap_filename, dpi=500)
			# plt.show()



			# Make a histogram of course sizes
			# plt.hist(class_sizes, bins=30)
			# plt.title("Course Size Histogram")
			# plt.xlabel("Course Size")
			# plt.ylabel("Count")
			# plt.show()


	def track(self):
		"""Unlike describe, this is used to track the output of the model, it will return values
		that can be used to track metrics for the sensitivity analysis"""

		# initilize highlevel tracker
		first_choices = 0
		second_choices = 0
		third_choices = 0

		# Initialize grade level tracker
		grade_first_choices = {}
		grade_second_choices = {}
		grade_third_choices = {}
		for i in range(5,13):
			grade_first_choices[i] = 0
			grade_second_choices[i] = 0
			grade_third_choices[i] = 0

		# record solution
		for i in range(len(self.STUDENTS)): # iterate over first X index
			for j in [1,2,3]: # iterate over second X index
				v = self.m.getVal(self.X[i,j]) # value of variable (either 1 or 0)
				if v == 1: # i.e. if assigned
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

		return [first_choices, second_choices, third_choices], grade_first_choices, grade_second_choices, grade_third_choices



if __name__=="__main__":

	s1, s2, s3, STUDENTS, COURSES = read_preference_data("Resources/FirstChoiceBinary.csv", 
		"Resources/SecondChoiceBinary.csv", "Resources/ThirdChoiceBinary.csv")
	MAX = read_MAX_data("Resources/CourseSize.csv")
	GRADES = read_grade_data("Resources/Grades.csv", STUDENTS)
	#print(COURSES)

	# check if you would like the run the basic test, i.e. just run the model per normal
	# if you say no will launch into a sensitivity check
	run_test = input("Run Test? (yes or no): ")
	#run_test = "yes"
	if run_test == "yes":
		s = ScheduleModel(s1, s2, s3, STUDENTS, COURSES, MAX, GRADES)
		s.set_objective([1000000,500,1])
		s.set_assignment_cons()
		s.set_max_cons()
		s.solve()
		s.describe_solution()
		quit() # terminate program


	print("Will give, and save, output for 3 different models, with " +
		"\n3 different weights for selections: [3,2,1], [10000, 50, 1], [10000000, 500, 1]")
	weights = [[3,2,1], [10000, 50, 1], [10000000, 500, 1]]
	for w in weights:
		s = ScheduleModel(s1, s2, s3, STUDENTS, COURSES, MAX, GRADES)
		s.set_objective(w) # specify the weight to be used
		s.set_assignment_cons()
		s.set_max_cons()
		s.solve()
		heatmap_filename = "heatmap_" + str(w) + "png"
		text_file_name = "text_" + str(w) +".txt"
		s.describe_solution(heatmap_filename=heatmap_filename, text_file_name=text_file_name)

	# end script
	quit()

























##############################################################################################
##############################################################################################

#								"main" code for sensitivity testings

##############################################################################################
##############################################################################################



	# # not testing, so run sensitivity check
	# import matplotlib.pyplot as plt
	# # first test is on first assignment weights
	# # the relevant test is changing distance between them
	# # lets first focus on distance between first and second, i.e. vary the 3 from 2.1 to 4 by .1
	
	# # initialize trackers
	# first = []
	# second = []
	# third = []
	# first_grade = {}
	# second_grade = {}
	# third_grade = {}
	# for g in range(5,13):
	# 	first_grade[int(g)] = []
	# 	second_grade[int(g)] = []
	# 	third_grade[int(g)] = []

	# for x in np.arange(2.1, 4.1, 0.1):
	# 	s = ScheduleModel(s1, s2, s3, STUDENTS, COURSES, MAX, GRADES)
	# 	s.set_objective([x,2,1])
	# 	s.set_assignment_cons()
	# 	s.set_max_cons()
	# 	s.solve()
	# 	[f, s, t], fc, sc, tc = s.track()
	# 	print(f,s,t)

	# 	# add results of this run to the trackers
	# 	first.append(f)
	# 	second.append(s)
	# 	third.append(t)
	# 	for g in range(5,13):
	# 		first_grade[g].append(fc[g])
	# 		second_grade[g].append(sc[g])
	# 		third_grade[g].append(tc[g])

	# # plot the results
	# plt.plot(np.arange(2.1, 4.1, 0.1), first, color='blue')
	# plt.plot(np.arange(2.1, 4.1, 0.1), second, color='red')
	# plt.plot(np.arange(2.1, 4.1, 0.1), third, color = 'green')
	# plt.xlabel("Value on first weight")
	# plt.legend()
	# plt.show()

	# # plot for each grade
	# for grade in range(5,13):
	# 	plt.plot(np.arange(2.1, 4.1, 0.1), first_grade[grade], label=str(grade))
	# plt.title("First Choices")
	# plt.legend()
	# plt.show()

	# for grade in range(5,13):
	# 	plt.plot(np.arange(2.1, 4.1, 0.1), second_grade[grade], label=str(grade))
	# plt.title("Second Choices")
	# plt.legend()
	# plt.show()

	# for grade in range(5,13):
	# 	plt.plot(np.arange(2.1, 4.1, 0.1), third_grade[grade], label=str(grade))
	# plt.title("Third Choices")
	# plt.legend()
	# plt.show()


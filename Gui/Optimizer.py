# Optimizer
# Kenneth Lipke
# Spring 2018

"""
Contains Optimizer class, which defines the main ILP
it has methods that parse the input data, set up variables,
constraints, and an objective--as well as solving.
It also contains methods to display the solution
"""

from pyscipopt import Model, quicksum
# from gurobipy import *
import numpy as np
import pandas as pd
from os import system
import pickle 
import timeit # just to check setuptime
import datetime

# Apparently need this to be used with tkinter?
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
#import matplotlib.pyplot as plt

from Requirement import *
from StudentMetadata import *

from Solution import *

class Optimizer():
	"""
	This class sets up a SCIP instance of our schedule optimization model
	it takes in various data files (in the form of Pandas DataFrames)
	It then extracts the relevant information and creates the model
	the various constraint groups are seperated and added by individual methods
	to help with debugging as input is changed

	There is a seperate method to run the optimization
	then there is a method to save the result

	There WILL BE methods to display and save the solutions in meaningful ways
	to users, such as saving text files with student schedules, master schedules
	etc.

	Main Fields
	-----------
	S - List of all students (currently just the student index)
	Cd - index --> course name dictinoary
	C - list of course indexies
	T - list of periods
	I - list of teachers (instructors)
	Db - list of flags for double period (the index is the course index)
	c_mini - list of indicies for courses that are not other or empty
	Grades - list of grades for each student (index corresponds to student)
	P - Prefernece matrix
	MIN - list of min course sizes
	MAX - list of MAX course sizes
	prox_dict - dictionary of proximities subject --> list of flags, where
				the index of the flag corrsponds to the course
				gets a 1 if it is in that subject
	multi_nested_list - list of lists, where each sub list is the courses that 
						are the same in multi-instance sense
	Ta - matrix of teachers and courses, gets a flag (1) if teacher is teaching
		that course. Teachers are rows, and courses are columns
	I_C_dict - dictionary of teacher name --> list of courses they teach
	R - list of rooms
	room_constrained_subjects - list of subjects that have room type constraints
	constrained_rooms - dictionary subject --> rooms that are OK for that sub
	constrained_courses - dictinoary subject --> courses constrained by that sub

	Main Methods
	------------
	add_basic constraints -- adds the basic constraints 
	add_course_constraints
	add_grade_lebel_requirements
	add_period_constraints
	add_proximity_constraints
	add_room_constraints
	add_teacher_constraints

	add_variables

	host of methods to get sets from the data 

	"""

	def __init__(self, prefs, LP_input, teacher, GAP, 
				student_dict, num_courses,
				rr_df = None,
				save_location=None,
				requirements = [],
				prox=None, ):
		"""
		Sets up main fields, and calls other methods to parse data into required
		sets

		Parameters
		----------
		prefs 	- a Pandas DataFrame containing the student preferences

		LP_Input- a Pandas DataFrame coming from a clean_data function, that serves
				  as the main input to the LP, it must have columns:
					Course Name
					Double Period
					Max
					Min
					Required Grades
					Number of Instances
					Room Type

		grades 	- a Pandas DataFrame that has all the students and their grade

		prox 	- a Padnas DataFrame that serves as the proximity matrix for courses

		teacher_info - a Padnas DataFrame that list all courses and the teacher
					   that will be teaching it

		Gap 	- the number from the GUI slider we will use to determine 
				  what MIPGap to run the solver with

		Requirements - List of requirement objects that were solicited from the user
					   these are then iterated over, parsed, and coded)

		"""

		# Initialze Fields
		self.S = None
		self.Cd = None
		self.C = None
		self.T = None
		self.I = None
		self.Db = None
		self.c_mini = None
		#self.Grades = None
		self.P = None
		self.MIN = None
		self.MAX = None
		self.prox_dict = None
		self.multi_nested_list = None
		self.Ta = None
		self.I_C_dict = None
		self.R = None
		self.room_constrained_subjects = None
		self.constrained_rooms = None
		self.constrained_courses = None
		self.RR_course_indicies = None # for the courses
		self.RR_student_dict = None # dictionary mapping RR to list of student indicies

		self.student_dict = student_dict
		self.num_courses = num_courses

		self.XV = {}
		self.CourseV = {}
		self.RoomV = {}
		self.UV = {}

		self.num_vars = 0
		self.num_cons = 0


		# main LP_input
		self.df = LP_input

		# Pulled from call
		self.teacher = teacher
		self.GAP = GAP
		self.requirements = requirements
		self.rr_df = rr_df # The dataframe with columns for rr's with student id's
		self.save_location = save_location

		# Clean up preferences (at least in current form)
		self.prefs = prefs.rename(columns={"Unnamed: 0": "Student"})

		# Place holders untill full data is made
		self.prox = prox
		#self.grades = grades
		#self.prox = pd.read_csv("../Resources/Proximity.csv")
		#self.grades = pd.read_csv("../Resources/grades.csv", header=None)

		# Pull sets
		self.pull_sets()

		# get multi-instance course list from main LP input
		self.get_multi_instance_course_list() # sets `multi_nested_list`

		# map teachers to courses
		self.map_teachers()

		# Get room data
		self.set_room_data()

		# Create model
		self.m = Model()

		# Quick shortening to see if it works?
		#self.S = self.S[-10:]
		#self.S = self.S[-140:]

		# Add Variables
		print("Adding Variables")
		self.add_variables()

		# # Add constraints
		# print("Adding Constraints")
		# self.add_basic_constraints()
		# self.add_max_constraint()
		# #self.add_min_constraint()
		# #self.add_proximity_constraints()
		# self.add_teacher_constraints()
		# self.add_course_constraints()
		# #self.add_grade_level_requirements()
		# self.add_room_constraints()
		# self.add_period_constraints()
		# print("Constraints Added")

		# self.set_objective()
		# You must explicitly call the optimize method to run




	def pull_sets(self):
		"""
		Pulls the sets:
			S   - Students
			Cd  - Course dictionary
			C   - Course indicies
			T 	- Periods
			I  	- Instructors
			Grades - Grades for each student
			P   - Preferences
			Db  - Double period flags
			c_mini - non-other/empty course indicies
			MIN - Min course sizes
			MAX - Max Course sizes
			prox_dict - prodimity dictionary for courses in same subject

		Saves them in the appropriate fields
		"""

		# Students
		# self.S = self.prefs["Student"].tolist() # list of all students (once we get ID make dictionary)
		self.S = list(self.prefs.index)

		# Courses
		self.Cd = {}
		#for i in self.df.index:
		for i in range(self.df.shape[0]): 
			self.Cd[i] = self.df["Course Name"].iloc[i]

		# # TEMP ADDITION
		# i = len(self.Cd)
		# self.Cd[i+1] = "RR1"
		# self.Cd[i+2] = "RR2"
		# self.Cd[i+3] = "RR3"

		self.C = range(len(self.Cd))

		# Gather "Other Indicies"
		self.other_indicies = []
		for j in self.Cd:
			if "Other" in self.Cd[j]:
				self.other_indicies.append(j)

		self.T = [1,2,3,4,7,8] # Periods

		# Instructors and corerspondence
		self.I = list(set(self.teacher["Teacher Name"]))

		# Grades for each student
		#self.Grades = self.grades['1']

		# Extract Preferences
		#self.P = self.prefs.drop("Student", axis=1).as_matrix()
		try:
			self.P = self.prefs.drop("Student", axis=1).as_matrix()
		except:
			# print("there is no Student column")
			# print("The columns are:", self.prefs.columns)
			# print("Moving on")
			self.P = self.prefs.as_matrix()
		self.P[self.P==1] = 4
		self.P[self.P==3] = 1
		self.P[self.P==4] = 3
		#self.P = self.prefs.as_matrix()

		# Double periods
		self.Db = self.df["Double Period"].fillna(0).astype(int)
		self.Db = self.Db.values

		# make set of course indicies without Other and Empty
		c_mini = []
		for j in self.Cd:
			if "Other" not in self.Cd[j] and "Empty" not in self.Cd[j]:
				c_mini.append(j)
		self.c_mini = c_mini

		# Course Sizes (min and max)
		self.MIN = self.df["Min"]
		self.MIN = self.MIN.values
		self.MAX = self.df["Max"]
		self.MAX = self.MAX.values

		# Proximity Matrix
		# self.D = prox.drop("0", axis=1).as_matrix() # <-- no longer that column
		self.D = self.prox.as_matrix()

		# Create Proximity dictionary {subject:proximity vector}
		self.prox_dict = {}
		Subjects = list(self.prox.columns)[1:]
		for subj in list(self.prox.columns)[1:]:
			self.prox_dict[subj] = self.prox[subj]

		# Get course indicies for the RR's
		# self.RR_course_indicies = []
		self.RR_course_indicies = {}
		for name in ["RR1", "RR2", "RR3"]:
			# self.RR_course_indicies.append(list(self.Cd.values()).index(name))
			self.RR_course_indicies[name] = list(self.Cd.values()).index(name)

		# Make the RR_dict from the rr_df
		print("The student dictionary has length:", len(self.student_dict))
		self.RR_student_dict = {}
		for name in ["RR1", "RR2", "RR3"]:
			l = list(self.rr_df[name])
			#print(l)
			l2 = []
			ind_list = []
			for v in l:
				if not np.isnan(v):
					l2.append(v)
			#print(v)


			for i in l2:
				#where i is a student ID
				#print("trying to find student id", i)
				for s in self.S:
					#print("working on student ind:", s)
					if not np.isnan(self.student_dict[s].s_id):
						if int(self.student_dict[s].s_id) == int(i):
							ind_list.append(s)
					else:
						pass

			self.RR_student_dict[name] = ind_list



	def get_multi_instance_course_list(self):
		"""
		sets the `multi_nested_list` field, determining which courses have multiple
		instances, used later to ensure that students are in at most one
		of the multiple instances
		"""
		multi = self.df["Number of Instances"].fillna(0).astype(int)
		multi=multi.values
		multi_nested_list = []
		j = 0
		while j < len(self.Cd):
			# if it is part of multi-instance cluster
			if multi[j] == 2:
			#print("testing multi[j] ==2 with j=", j, "multi[j]=",multi[j])
			#if int(multi.get(j)) == 2:
				# if it is a double period
				if self.Db[j] == 1:
					new = [j, j+2]
					j += 4 # pass over cluster
				else:
					# not a double period
					new = [j, j+1]
					j += 2
				multi_nested_list.append(new)
			# if not a multi-instance  
			elif multi[j] == 3:
				# these can't be double periods so just drop in all 3
				multi_nested_list.append([j, j+1, j+2])
				j += 3 
			else:
				j += 1

			# we ignore > 3, as this is Other

		# set field
		self.multi_nested_list = multi_nested_list


	def map_teachers(self):
		"""
		Maps teachers to their courses, 
		creates the fields
			I_C_dict - dictinoary style mapping
			Ta - matrix flag style mapping
		"""
		# Need matrix with instructors as rows, all courses as columns, and 1 if teaching that course
		I_C_dict = {}
		for i in self.I:
			I_C_dict[i] = []
			for index in range(self.teacher.shape[0]):
				if self.teacher.iloc[index]["Teacher Name"] == i:
					l = I_C_dict[i]
					#l.append(self.teacher.iloc[index][1])
					l.append(self.teacher.iloc[index]["Course Name"])
					I_C_dict[i] = l


		# Teacher_Course_Matrix 
		courses_list = list(self.Cd.values())
		Teacher_Course_Matrix = np.zeros(len(courses_list))
		for i in self.I:
			t = np.zeros(len(courses_list))
			for j in self.Cd:
				if self.Cd[j] in I_C_dict[i]:
					# print(i, "is teaching:", (40-len(i)-12)*".", Cd[j])
					t[j] =1
			Teacher_Course_Matrix = np.vstack([Teacher_Course_Matrix, np.matrix(t)])

		Ta = np.array(Teacher_Course_Matrix[1:]) # matrix tying teachers to courses they teach

		# Save fields
		self.Ta = Ta
		self.I_C_dict = I_C_dict

	def set_room_data(self):
		"""
		Sets up the room data, 
			R - Set of all Rooms (which we take as given)
			room_constrained_subjects - list of subjects that require special rooms
			constrainted_rooms - dictionary of rooms that meet constraints
									subject:room
			constrained_courses - dictinoary of courses that need certain rooms
									subject:list[courses]
		"""
		# Set of rooms
		R = ["U1", "Steve", "U2", "U3", "U4/5", "U6", "U7", "L2", "L3", "Library", "Art", "L4", 
				"L6", "Sci A", "Sci B", "Sci C", "Music Room", "Gym", "Gym2",
				"RR1", "RR2", "RR3"]

		# Department Courses
		Science_Rooms = ["Sci A", "Sci B", "Sci C"]
		Art_Rooms = ["Art"]
		Gym_Rooms = ["Gym", "Gym2"]
		Music_Rooms = ["Music Room"]
		Resource_Rooms = ["RR1", "RR2", "RR3"]
		Free_Rooms = list( set(R) - set(Science_Rooms + Art_Rooms + Gym_Rooms +
			Music_Rooms))

		# Get courses for each room type (Art, Science, Gym, Music, Resource)
		Art_Courses = self.df.index[self.df['Room Type'] == "Art"].tolist()
		Science_Courses = self.df.index[self.df['Room Type'] == "Science"].tolist()
		Gym_Courses = self.df.index[self.df['Room Type'] == "Gym"].tolist()
		Music_Courses = self.df.index[self.df['Room Type'] == "Music"].tolist()
		Resource_Courses = self.df.index[self.df['Room Type'] == "Resource"].tolist()

		room_constrained_subjects = ["Science", "Art", "Music", "Gym", "Resource"]
		constrained_rooms = {"Science":Science_Rooms, "Art":Art_Rooms, 
			"Music":Music_Rooms, "Gym":Gym_Rooms, "Resource":Resource_Rooms}
		constrained_courses = {"Science":Science_Courses, "Art":Art_Courses,
			"Music":Music_Courses, "Gym":Gym_Courses, "Resource":Resource_Courses}

		# set fields
		self.R = R
		self.room_constrained_subjects = room_constrained_subjects
		self.constrained_rooms = constrained_rooms
		self.constrained_courses = constrained_courses


	def add_variables(self):
		"""
		Adds the model variables:
			X[student, course] - Student Variable
			Course[course, period] - Course Variable
			U[student, course, period] - Cross-over var
			Rv[course, room, period] - Room var
		"""
		# Add Student Variables (X)
		X = {}
		for i in self.S:
			for j in range(len(self.C)):
				name = "Student " + str(i) + " in course " + str(j)
				# X[i,j] = m.addVar(vtype=GRB.BINARY, name=name)
				X[i,j] = self.m.addVar(vtype="B", name=name)
				self.num_vars += 1
		print("\tStudent/Course variable added")

		# Add Course Variable
		Course = {} # Variable dictionary
		for j in range(len(self.C)):
			for t in self.T:
				name = "Course " + str(j) + " in period " + str(t)
				# Course[j,t] = m.addVar(vtype=GRB.BINARY, name=name)
				Course[j,t] = self.m.addVar(vtype="B", name=name)
				self.num_vars += 1
		print("\tCourse/Period variable added")

		# Create the u variable
		U = {}
		for i in self.S:
			for j in range(len(self.C)):
				for t in self.T:
					name = "min " + str(i) + ", " + str(j) + ", " + str(t)
					# U[i,j,t] = m.addVar(vtype=GRB.BINARY, name=name)
					U[i,j,t] = self.m.addVar(vtype="B", name=name)
					self.num_vars += 1
		print("\tU(Student/Course/Period) variable added")

		# Define r  room variable (over course j in room r durring period t)
		Rv = {}
		for j in range(len(self.C)):
			if "Other" not in self.Cd[j] and "Empty" not in self.Cd[j]:
				for s in self.R:
					for t in self.T:
						name = "Course " + str(j) + " in room " + str(s) + \
								" durring period " + str(t)
						# Rv[j,s,t] = m.addVar(vtype=GRB.BINARY, name=name)
						Rv[j,s,t] = self.m.addVar(vtype="B", name=name)
						self.num_vars += 1
		print("\tRoom/Period Variables added")

		# Save to class
		self.X = X
		self.Course = Course
		self.U = U
		self.Rv = Rv


	def add_basic_constraints(self):
		"""
		Adds the basic constraints to the model:
			Students in one course per period (using U variable)
			Constraint enfocing U variable definition
			Min and Max capacity constriants
		"""
		# Force student in one course per period
		for i in self.S:
			for t in self.T:
				# m.addConstr(quicksum(U[i,j,t] for j in C) == 1) # one course per period
				self.m.addCons(quicksum(self.U[i,j,t] for j in self.C) == 1) # one course per period
				self.num_cons += 1
		print("\tOne course per period")


		# "AND" Constraint--no more than one course per period for a student
		# Enforces the definition of the U variable
		for i in self.S:
			for j in self.C:
				# m.addConstr(X[i,j] == quicksum(U[i,j,t] for t in T))
				self.m.addCons(self.X[i,j] == quicksum(self.U[i,j,t] for t in self.T))
				self.num_cons += 1
				for t in self.T:
					# m.addConstr(Course[j,t] >= U[i,j,t])
					self.m.addCons(self.Course[j,t] >= self.U[i,j,t])
					self.num_cons += 1
		print("\tU set-up constraints (`and`) added")


	def add_max_constraint(self):
		"""
		Adds max capacity constraint
		"""
		for j in range(len(self.C)):
			self.m.addCons(quicksum(self.X[i,j] for i in self.S) <= self.MAX[j])
			self.num_cons += 1
		print("\tMax course capacity")


	def add_min_constraint(self):
		"""
		Adds min capacity constraint
		"""
		for j in range(len(self.C)):
			self.m.addCons(quicksum(self.X[i,j] for i in self.S) >= self.MIN[j])
			self.num_cons += 1
		print("\tMin capacity constraint")


	def add_proximity_constraints(self):
		"""
		Adds the proximity constraints
		"""

		# Setup proximity min and max dicts (temp untill we generate more granular data)
		# min_sub_dict = {}
		# max_sub_dict = {}
		# for subject in self.prox_dict.keys():
		# 	min_sub_dict[subject] = np.ones(len(self.S))*0
		# 	max_sub_dict[subject] = np.ones(len(self.S))*3 

		# for subject in self.prox_dict.keys():
		# 	if subject != "Other":
		# 		for i in self.S:
		# 			# Only add the minimum constraint if meaningful
		# 			if min_sub_dict[subject][i] > 0:
		# 				self.m.addCons(quicksum(self.prox_dict[subject][j]*self.X[i,j]
		# 				 for j in range(len(self.C))) >= min_sub_dict[subject][i])

		# 			# Always add the max constraint
		# 			self.m.addCons(quicksum(self.prox_dict[subject][j]*self.X[i,j]
		# 						 for j in self.C) <= max_sub_dict[subject][i])

		for subject in self.num_courses.keys():
			#if (subject not in  ["Other", "J"] and (subject in self.num_courses.keys()) ):
			if subject in self.num_courses.keys():
				print("\t\t", subject)
				#d = self.num_courses[subject] # easy reference to list
				for i in self.S:
					# Only add the minimum constraint if meaningful
					#if d[i] > 0:
					# make sure they don't request too many
					#pm = np.sum(self.prox_dict[subject]) # number possible 
						# courses that satisfy req
					#lim = np.min([pm, d[i]]) # min(# they want, # possible)
					#if subject == "IB":
						#print("\t\t\tlimit:", lim)
					#self.m.addCons(quicksum(self.prox_dict[subject][j]*self.X[i,j]
					# for j in self.C) >= lim) # was == but >= might be faster
		
					#------------------------------------------------------
					#					Come Back to This
					#------------------------------------------------------
					# This is pissy as prox not updated for new RR courses
					# I will comment this out and try somethign else as a TEMP fix
					try:
						self.m.addCons(quicksum(self.prox_dict[subject][j]*self.X[i,j]
							for j in self.C) <= 2) # was == but >= might be faster
						self.num_cons += 1
					except:
						pass

					# mini = range(len(self.Cd)-3) # as there are 3 RR's
					# self.m.addCons(quicksum(self.prox_dict[subject][j]*self.X[i,j]
					# 	for j in mini) <= 2) # was == but >= might be faster
		print("\tProximity constraint added")





	def add_teacher_constraints(self):
		"""
		Adds the teacher constraints:
			teacher teaches at most one course per period
		"""
		# Teacher teaching at most one course per period
		for k in range(len(self.I)):
			for t in self.T:
				# m.addConstr(quicksum(Course[j,t]*Ta[k][j] for j in C) <= 1)
				if np.sum(self.Ta[k]) > 0:
					self.m.addCons(quicksum(self.Course[j,t]*self.Ta[k][j] for j in self.C) <= 1)
					self.num_cons += 1
		print("\tTeacher teaches as most once per period")


	def add_course_constraints(self):
		"""
		Adds the course constraints:
			Each course taught only once
			Double period courses are taught consecutively (and no tin 4 or 8)
			Students in both parts of the double
			Students in at most 1 of the multi-instance sections
		"""
		# Course Taught only once Constraint
		for j in range(len(self.C)):
			# m.addConstr(quicksum(Course[j,t] for t in T) == 1)
			self.m.addCons(quicksum(self.Course[j,t] for t in self.T) == 1)
			self.num_cons += 1
		print("\tCourse taught only once")

		# Double period--consecutive constraints
		for j in range(len(self.C)):
			if self.Db[j] == 1: # if double period
				for t in self.T:
					if t != 4 and t != 8:
						# m.addConstr(Course[j,t] == Course[j+1, t+1]) # change to == from >= 
						self.m.addCons(self.Course[j,t] == self.Course[j+1, t+1]) # change to == from >= 
						self.num_cons += 1
		print("\tDouble periods must be consecutive")


		# Double Period--not 4th or 8th
		for j in range(len(self.C)):
			if self.Db[j] == 1:
				# m.addConstr(Course[j,4] == 0)
				self.m.addCons(self.Course[j,4] == 0)
				self.num_cons += 1
				# m.addConstr(Course[j,8] == 0)
				self.m.addCons(self.Course[j,8] == 0)
				self.num_cons += 1
		print("\tDouble periods not in 4th or 8th")


		# # Double Period--Student in both
		for i in self.S:
			for j in range(len(self.C)):
				if self.Db[j] == 1:
					# m.addConstr(X[i,j+1] == X[i,j]) # this was >= but == is better?
					self.m.addCons(self.X[i,j+1] == self.X[i,j]) # this was >= but == is better?
					self.num_cons += 1
		print("\tStudents in both parts of double")

		# Multi-Instance courses (students only in one instance--at most)
		for i in self.S:
			for course_set in self.multi_nested_list:
				# in at most one course of the list
				# m.addConstr(quicksum(X[i,j] for j in course_set) <= 1)
				self.m.addCons(quicksum(self.X[i,j] for j in course_set) <= 1)
				self.num_cons += 1
		print("\tStudents in at most of instance of multi-instance Course ")



	def add_grade_level_requirements(self):
		"""
		Adds theg grade level requirements that are specified via the GUI
		"""
		# Get list of course names to find index later
		l = list(self.Cd.values())

		for req in self.requirements:
			# get indicies for courses:
			index1 = l.index(req.course1)
			if req.course2 is not None:
				index2 = l.index(req.course2)
			else:
				index2 = None

			# determine if multi-index course
			multi_1 = [index1] #<-- therefore can use even if not multi later
			if index2 is not None:
				multi_2 = [index2]
			for m in self.multi_nested_list:
				if index1 in m:
					multi_1 = m # <-- contains list of indicies that also qualify
				if (index2 is not None) and (index2 in m):
					multi_2 = m

			# Combine the two index lists (if there are two)
			if index2 is not None:
				multi = multi_1 + multi_2
			else:
				multi = multi_1

			# Add constraint
			for i in self.S:
				#if self.Grades[i] == req.grade:
				# New way of pulling grade out of dictinary
				if self.student_dict[i].grade == req.grade:
					self.m.addCons(quicksum(self.X[i,j] for j in multi) == 1)
					self.num_cons += 1



	def add_room_constraints(self):
		"""
		Adds the room constraints:
			If taught, gets one room
			Room gets at most one course per period
			Double periods taught in the same room
			Room constrainted courses accomodated
		"""


		# If course taught, gets one room
		for j in range(len(self.C)):
			if "Other" not in self.Cd[j] and "Empty" not in self.Cd[j]:
				for t in self.T:
					# m.addConstr(quicksum(Rv[j,s,t] for s in R) == Course[j,t])
					self.m.addCons(quicksum(self.Rv[j,s,t] for s in self.R) 
						== self.Course[j,t])
					self.num_cons += 1
		print("\tCourses get one room")


		# Room gets at most one course per period
		for s in self.R:
			for t in self.T:
				# m.addConstr(quicksum(Rv[j,s,t] for j in c_mini) <= 1)
				#self.m.addCons(quicksum(self.Rv[j,s,t] for j in self.c_mini) <= 1) # <---- this is when there are Other courses included 
				self.m.addCons(quicksum(self.Rv[j,s,t] for j in self.C) <= 1)
				self.num_cons += 1
		print("\tRooms get at most one course per period")

		# Double periods in the same room
		for j in self.Cd:
			if self.Db[j] == 1:
				for t in self.T:
					if t != 4 and t != 8:
						for s in self.R:
							# m.addConstr(Rv[j,s,t] == Rv[j+1, s, t+1])
							self.m.addCons(self.Rv[j,s,t] == self.Rv[j+1, s, t+1])
							self.num_cons += 1
		print("\tDouble Periods in same room")


		# Subject specific courses get correct rooms
		#test = ['Science', 'Art', 'Music', 'Gym']
		for subject in self.room_constrained_subjects:
		#for subject in test:
			sub_courses = self.constrained_courses[subject] # coruses in this subject
			sub_rooms = self.constrained_rooms[subject] # appropriate rooms
			for j in sub_courses:
				for t in self.T:
					# m.addConstr(quicksum(Rv[j,s,t] for s in sub_rooms) == Course[j,t])
					self.m.addCons(quicksum(self.Rv[j,s,t] for s in sub_rooms)
						 == self.Course[j,t])
					self.num_cons += 1
		print("\tCourses with subject specific room needs accomodated")

		# Special rooms don't get other types of courses
		#for subject in ['Art', 'Music', 'Gym']:
		for subject in ['Art', 'Music', 'Gym', "Resource"]:
			rooms = self.constrained_rooms[subject]
			sub_courses = set(self.constrained_courses[subject])
			#non_sub_courses = list(set(self.c_mini) - sub_courses) # set minus
			non_sub_courses = list(set(self.C) - sub_courses) # set minus <------ when other courses included
			# ^^ courses that cannot be in these rooms
			for j in non_sub_courses:
				for t in self.T:
					for s in rooms:
						self.m.addCons(self.Rv[j,s,t] == 0)
						self.num_cons += 1
		print("\tReverse subject constrained rooms enforced")

	def add_rr_constraints(self):
		"""
		Adds the resource room requirement
		"""
		for r in ["RR1", "RR2", "RR3"]:
			students = self.RR_student_dict[r]
			course = self.RR_course_indicies[r]
			for i in self.S:
				if i in students:
					# This student must be in the resource room
					self.m.addCons(self.X[i,course] == 1)
					self.num_cons += 1
				else:
					# student not allowed in resource room
					self.m.addCons(self.X[i,course] == 0)
					self.num_cons += 1

		print("\tAdded RR constraint")




	def add_period_constraints(self):
		"""
		Adds the period constraints
			`other` in appropriate period
		"""
		# Force "Other" courses in specific periods
		for i in range(len(self.T)):
			# m.addConstr(Course[other_indicies[i], T[i]] == 1)
			self.m.addCons(self.Course[self.other_indicies[i], self.T[i]] == 1)
			self.num_cons += 1
		print("\t`Other` courses in each period")


	def set_objective(self):
		"""
		Sets the objective
			Minimizes the number of others, while
			maximizing the preference score
		also sets the GAP
		"""
		if self.GAP is not None:
			self.m.setRealParam('limits/gap', self.GAP)
		else:
			self.m.setRealParam('limits/gap', .33)
		print("GAP set at", self.GAP)

		# Set up senority multiplier
		s = {}
		for i in self.S:
			g = self.student_dict[i].grade
			# print("In grade:", g)
			if g in [7,11]:
				s[i] = 2
				#print("\t2")
			elif g in [8,12]:
				s[i] = 4
				#print("\t4")
			elif g in [6]:
				s[i] = 1000
			else:
				s[i] = 1
				#print("\t1")
		#print(s)

		# Make a copy of the preference matrix that puts all the zeros 
		# with -10's
		P2 = self.P.copy()
		P2[P2==1] = 3
		P2[P2==2] = 4
		P2[P2==3] = 5
		self.Ptest = P2
		print(P2)

		#-------------------------------------------------------
		#						Fix This!!
		#-------------------------------------------------------
		# prox has wrong dimensions as it does not have 
		# enough columns for the new RR courses
		# for the moment mini should work, but we need to fix this
		# where it was self.C I put mini as a temp fix
		mini = range(len(self.C) - 3)
		self.m.setObjective(-1*quicksum(self.X[i,j] for i in self.S 
			for j in self.other_indicies) + 
			quicksum(s[i]*self.X[i,j]*P2[i][j] for i in self.S 
			for j in mini), "maximize")


		# Quick test with just 6th graders without senority
		# self.m.setObjective(-1*quicksum(self.X[i,j] for i in self.S 
		# 	for j in self.other_indicies) + 
		# 	quicksum(self.X[i,j]*self.P[i][j] for i in self.S 
		# 	for j in O.C), "maximize")
		# print("Objective Set")

	def optimize(self):
		"""
		Runs the optimization sequence
		"""
		print("Optimizing with", len(self.S), "students")
		print("Saving to", self.save_location)
		print("-"*30 + " Optimization Starting " + "-"*30)
		print("Number of variables:", self.num_vars)
		print("Number of constraints:", self.num_cons)
		start_time = datetime.datetime.now()
		print("Optimization start time:", start_time)
		self.m.optimize()

	def assign_value_dicts(self):
		"""
		Once the optimization is completed, call this function
		to fill in the following dictionaries
			XV
			CourseV
			RV
			UV
		"""
		XV = {}
		CourseV = {}
		for i in self.S:
			for j in range(len(self.C)):
				# get student variable
				XV[i,j] = self.get_value(self.X[i,j])
				for t in self.T:
					CourseV[j,t] = self.get_value(self.Course[j,t])
		# get rooms
		RoomV = {}
		# for j in range(len(C)):
		#for j in self.c_mini: #<------ when there are other courses included
		for j in self.C:
			for s in self.R:
				for t in self.T:
					RoomV[j,s,t] = self.get_value(self.Rv[j,s,t])

		UV = {}
		for i in self.S:
			for j in self.Cd:
				for t in self.T:
					UV[i,j,t] = self.get_value(self.U[i,j,t])

		# assign fields
		self.XV = XV
		self.CourseV = CourseV
		self.RoomV = RoomV
		self.UV = UV


	def get_value(self, var):
		"""
		Takes in a variable, and if the model is done running,
		will return the value.
		Deals with SCIP being weird about binary variables
		"""
		v = self.m.getVal(var)
		if v < 0.75:
			return 0
		else:
			return 1

	def get_enrollment(self, course):
		"""
		takes in a course index corrseponding to a course in Cd
		and returns the number of students enrolled
		Note: Assumes the variable value dictionaries have already been defined
		"""
		num_enrolled = 0
		for i in self.S:
			if self.XV[i,course] == 1:
				num_enrolled += 1
		return num_enrolled


	def get_teacher(self, course):
		"""
		Takes in a course ID and retunrs the teachers name
		"""
		for k in range(len(self.I)):
			if self.Ta[k][course] == 1:
				return self.I[k]
		# if no teacher (other, or empty)
		return ""

	def get_room(self, course, period):
		"""
		Returns string of room that `course` is taugh in durring `period`
		Note: Value dictionries must be filled in
		"""
		if "Other" in self.Cd[course] or "Empty" in self.Cd[course]:
			return "N/A"
		for s in self.R:
			if self.RoomV[course, s, period] == 1:
				return s

	def print_grid(self):
		"""
		Prints the grid version of schedule with info
		Note: dictionaries must be filled in
		"""
		print("\n\n")
		for t in self.T:
			print("-"*20 + " " + "PERIOD " + str(t) + " " + "-"*110)
			print("Room" + 36*" " + "Course" + 34*" " + "Enrollment" + " "*(40 - len("Enrollment")) + "Teacher")
			print("-"*140)
			# for j in range(len(C)):
			#for j in self.c_mini: #<----- when there are other courses included
			for j in self.C:
				# if the course is offered
				if self.CourseV[j,t] == 1:
					# figure out which room
					for s in self.R:
						if self.RoomV[j,s,t] == 1:
							num_enrolled = self.get_enrollment(j)
							print(s + (40 - len(s))*"." + self.Cd[j] + (40 - len(self.Cd[j]))*"." \
								+ str(num_enrolled) + "."*(40 - len(str(num_enrolled))) + self.get_teacher(j))
			print("\n")

	def print_grid_no_room(self):
		"""
		prints the gride version of schedule
		this version of the function is to be called if the 
		model is run without the room constrains
		"""
		print("\n\n")
		for t in self.T:
			print("-"*20 + " " + "PERIOD " + str(t) + " " + "-"*70)
			print("Course" + 34*" " + "Enrollment" + " "*(40 - len("Enrollment")) + "Teacher")
			print("-"*100)
			# for j in range(len(C)):
			#for j in self.c_mini:
			for j in self.C:
				# if the course is offered
				if self.CourseV[j,t] == 1:
					num_enrolled = self.get_enrollment(j)
					print(self.Cd[j] + (40 - len(self.Cd[j]))*"." \
						+ str(num_enrolled) + "."*(40 - len(str(num_enrolled))) + self.get_teacher(j))
			print("\n")

	def save_grid(self, file_name="grid.txt"):
		"""
		Takes in a file name, and saves the grid to a text file at that location
		Largely, mirrors the print_grid function, just with saves

		Expected that file has .txt extension already
		"""
		if self.save_location is not None:
			file_name = self.save_location + "/" + file_name
		file = open(file_name, "w")
		for t in self.T:
			file.write("-"*20 + " " + "PERIOD " + str(t) + " " + "-"*110 + "\n")
			file.write("Room" + 36*" " + "Course" + 34*" " + "Enrollment" + " "*(40 - len("Enrollment")) + "Teacher" + "\n")
			file.write("-"*140 + "\n")
			# for j in range(len(C)):
			#for j in self.c_mini:
			for j in self.C:
				# if the course is offered
				if self.CourseV[j,t] == 1:
					# figure out which room
					for s in self.R:
						if self.RoomV[j,s,t] == 1:
							num_enrolled = self.get_enrollment(j)
							file.write(s + (40 - len(s))*"." + self.Cd[j] + (40 - len(self.Cd[j]))*"." \
								+ str(num_enrolled) + "."*(40 - len(str(num_enrolled))) + self.get_teacher(j) + "\n")
			file.write("\n")


	def save_grid_no_rooms(self, file_name):
		"""
		Takes in a file name, and saves the grid to a text file at that location
		Largely, mirrors the print_grid function, just with saves

		Expected that file has .txt extension already
		"""
		if self.save_location is not None:
			file_name = self.save_location + "/" + file_name
		file = open(file_name, "w")
		for t in self.T:
			file.write("-"*20 + " " + "PERIOD " + str(t) + " " + "-"*70 + "\n")
			file.write("Course" + 34*" " + "Enrollment" + " "*(40 - len("Enrollment")) + "Teacher" + "\n")
			file.write("-"*100 + "\n")
			# for j in range(len(C)):
			#for j in self.c_mini:
			for j in self.C:
				# if the course is offered
				if self.CourseV[j,t] == 1:
						num_enrolled = self.get_enrollment(j)
						file.write(self.Cd[j] + (40 - len(self.Cd[j]))*"." \
							+ str(num_enrolled) + "."*(40 - len(str(num_enrolled))) + self.get_teacher(j) + "\n")
			file.write("\n")



	def print_student_schedule(self, student, show_score=False):
		"""
		takes in the index of a student and prints out their schedule
		"""
		# Get students grade
		#g = self.Grades[student]
		g = self.student_dict[student].grade
		last_name = self.student_dict[student].last_name
		first_name = self.student_dict[student].first_name
		print(first_name + " " + last_name + " (grade " + str(g) + ")")
		if show_score:
			print("Score:", self.get_score(student))
		print("-"*85)
		for t in self.T:
			for j in self.Cd:
				if self.XV[student,j] == 1 and self.CourseV[j,t] == 1:
					room = self.get_room(j,t)
					teacher = self.get_teacher(j)
					s1 = "Period " + str(t) + ": " + self.Cd[j]
					#print "Period " + str(t) + ": " + Cd[j]
					print( s1 + ((50-len(s1))*".") + room + ((20-len(room))*".") + teacher)


	def print_student_schedule_no_room(self,student):
		g = self.student_dict[student].grade
		last_name = self.student_dict[student].last_name
		first_name = self.student_dict[student].first_name
		print(first_name + " " + last_name + " (grade " + str(g) + ")")
		print("-"*65)
		for t in self.T:
			for j in self.Cd:
				if self.XV[student,j] == 1 and self.CourseV[j,t] == 1:
					teacher = self.get_teacher(j)
					s1 = "Period " + str(t) + ": " + self.Cd[j]
					#print "Period " + str(t) + ": " + Cd[j]
					print( s1 + ((50-len(s1))*".")  + teacher)


	def save_student_schedule(self, student, file_name, show_score=False):
		"""
		Takes in an index of a student, as well as the name of .txt file, 
		and saves the student's schedule to the new text file

		Expects that file_name has a .txt extension already
		"""
		file = open(file_name, "w")

		#g = self.Grades[student]
		g = self.student_dict[student].grade
		last_name = self.student_dict[student].last_name
		first_name = self.student_dict[student].first_name
		file.write(first_name + " " + last_name + " (grade " + str(g) + ")" + "\n")
		if show_score:
			file.write("Score: " + str(self.get_score(student)) + "\n")
		file.write("-"*85 + "\n")
		for t in self.T:
			for j in self.Cd:
				if self.XV[student,j] == 1 and self.CourseV[j,t] == 1:
					room = self.get_room(j,t)
					teacher = self.get_teacher(j)
					s1 = "Period " + str(t) + ": " + self.Cd[j]
					#print "Period " + str(t) + ": " + Cd[j]
					file.write( s1 + ((50-len(s1))*".") + room + ((20-len(room))*".") + teacher + "\n")

	def save_student_schedule_no_rooms(self, student, file_name):
		"""
		Takes in an index of a student, as well as the name of .txt file, 
		and saves the student's schedule to the new text file

		Expects that file_name has a .txt extension already
		"""
		file = open(file_name, "w")

		#g = self.Grades[student]
		g = self.student_dict[student].grade
		last_name = self.student_dict[student].last_name
		first_name = self.student_dict[student].first_name
		file.write(first_name + " " + last_name + " (grade " + str(g) + ")" + "\n")
		file.write("-"*65 + "\n")
		for t in self.T:
			for j in self.Cd:
				if self.XV[student,j] == 1 and self.CourseV[j,t] == 1:
					teacher = self.get_teacher(j)
					s1 = "Period " + str(t) + ": " + self.Cd[j]
					#print "Period " + str(t) + ": " + Cd[j]
					file.write( s1 + ((50-len(s1))*".") + teacher + "\n")


	def print_all_student_schedules(self, rooms=True, show_score=False):
		"""
		Prints all student schedules

		rooms - Boolean, indicates if the model was run with or without rooms
		"""
		for s in self.S:
			print("student", s, "grade", self.student_dict[s].grade, "is type", type(self.student_dict[s].grade))
			if not np.isnan(self.student_dict[s].grade):
				if rooms:
					self.print_student_schedule(s)
				else:
					self.print_student_schedule_no_room(s)
			print("\n\n")

	def save_all_student_schedules(self, rooms = True, show_score=False):
		"""
		Saves all student schedules as text files
		"""
		for s in self.S:
			if not np.isnan(self.student_dict[s].grade):
				last_name = self.student_dict[s].last_name
				first_name = self.student_dict[s].first_name
				f = last_name + "_" + first_name + "_schedule.txt"
				if self.save_location is not None:
					f = self.save_location + "/" +f
				if rooms:
					self.save_student_schedule(s, f, show_score=show_score)
				else:
					self.save_student_schedule_no_rooms(s, f)

	def diagnostic(self):
		"""
		gives a preference score for each student, and indicates, if they
		were assigned to any course the did not want
		"""
		for i in self.S:
			name = (self.student_dict[i].first_name + 
						self.student_dict[i].last_name)
			pref_score = 0
			bad_assignments = []
			for j in self.C:
				# if assigned to course
				if self.XV[i,j] == 1:
					# did they want it?
					if self.P[i,j] > 0 :
						pref_score += self.P[i,j]
					else:
						# need to make sure not second half of double
						d = 0
						try:
							if self.Db[j-1] == 1:
								d += 1
						except:
							pass

						if d == 0:
							# then it was a bad assignment
							bad_assignments.append(self.Cd[j])

			s = "Student " + str(i) + " gets score " + str(pref_score)
			if bad_assignments != []:
				s += " (badly assigned to " + str(bad_assignments) + ")"
			print(s)

	def get_score(self, i):
		"""
		gets the score for a student index i
		"""
		s = 0
		for j in self.C:
			if self.XV[i,j] == 1:
				s += self.P[i][j]
		return s

	def save_dicts(self):
		"""
		Saves the variable dictionaries to the save_location folder
		"""
		print("Pickling solutions")
		at = self.save_location
		pickle.dump(self.XV, open(at+"/xv.pkl", 'wb'), pickle.HIGHEST_PROTOCOL)
		pickle.dump(self.CourseV, open(at+"/coursev.pkl", 'wb'), pickle.HIGHEST_PROTOCOL)
		pickle.dump(self.RoomV, open(at+"/roomv.pkl", 'wb'), pickle.HIGHEST_PROTOCOL)
		pickle.dump(self.UV, open(at+"/uv.pkl", 'wb'), pickle.HIGHEST_PROTOCOL)

	def make_hist(self, name="score_hist.png", save=True):
		"""
		Makes histogram of scores
		"""
		# # Make a histogram of scores
		scores = []
		for i in self.S:
			s = 0
			for j in self.C:
				if self.XV[i,j] == 1:
					s += self.P[i][j]
			scores.append(s)
		plt.hist(scores, bins=18)
		plt.title("Histogram of Student Scores")
		plt.xlabel("Score")
		if save:
			plt.savefig(self.save_location +"/" + name, dpi=300)
			plt.clf()
		else:
			plt.show()
			plt.clf()

	def plot_score_by_grade(self, name="scorce_grade.png", save=True):
		"""
		Makes plot showing score breakdown by grade
		"""
		# Score by Grade plot
		sg = {}
		for g in [5,6,7,8,9,10,11,12]:
			sg[g] = []
			for i in self.S:
				if self.student_dict[i].grade == g:
					sg[g].append(self.get_score(i))

		for g in [5,6,7,8,9,10,11,12]:
			l = "Grade " + str(g)
			plt.scatter(g*np.ones(len(sg[g])), sg[g], label=l, alpha=.35)
			avg = np.mean(sg[g])
			plt.plot(g, avg, color="red", marker="_", ms=25)
		plt.xlabel("Grade")
		plt.ylabel("Score")
		plt.title("Scores by Grade")
		if save:
			plt.savefig(self.save_location + "/score_grade.png", dpi=400)
			plt.clf()
		else:
			plt.show()
			plt.clf()

if __name__ == "__main__":
	"""
	Quick running tester
	"""

	# gets files
	# LP_input = pd.read_csv("OptTestFiles/LP_input2.csv")
	# teacher = pd.read_csv("OptTestFiles/teacher2.csv")
	# prefs = pd.read_csv("OptTestFiles/prefs2.csv")
	# #grades = pd.read_csv("OptTestFiles/grades.csv")
	# grades = pd.DataFrame({'0':[1,2], '1':[8,9]})
	# prox =pd.read_csv("OptTestFiles/prox2.csv")


	#LP_input = pd.read_csv("test_LP_input.csv")
	#LP_input = pd.read_csv("~/Desktop/test_pref/LP_input.csv") # most recent
	LP_input = pd.read_csv("~/Desktop/test_pref/LP_Input4.csv") # was 4
	#teacher = pd.read_csv("test_teacher_Df.csv") # most recent
	teacher = pd.read_csv("~/Desktop/test_pref/Teacher_Template_filled2.csv") # was 2
	#prefs = pd.read_csv("test_pref_input_df.csv") 
	prefs = pd.read_csv("~/Desktop/test_pref/processed_preference_data2.csv") # waz 2
	#grades = pd.read_csv("OptTestFiles/grades.csv")
	#grades = pd.DataFrame({'0':range(1,prefs.shape[0] +1), '1':10*np.ones(prefs.shape[0])})
	prox =pd.read_csv("~/Desktop/test_pref/Proximity3.csv") # before without 2 # was 3

	# Get student dictionary
	# hs_prefs = pd.read_csv("~/Desktop/test_pref/High School Form2.csv")
	# ms_prefs = pd.read_csv("~/Desktop/test_pref/Middle School form2.csv")
	ms_prefs = pd.read_csv("~/Desktop/test_pref/ms_response.csv")
	hs_prefs = pd.read_csv("~/Desktop/test_pref/hs_response.csv")

	# From real_data---------------------------------------------
	LP_input = pd.read_csv("~/Desktop/test_pref/real_data/LP_Input.csv")
	teacher = pd.read_csv("~/Desktop/test_pref/real_data/Teacher_Template_filled.csv")
	prox =pd.read_csv("~/Desktop/test_pref/real_data/Proximity.csv")
	prefs = pd.read_csv("~/Desktop/test_pref/real_data/processed_preference_data_index_fix.csv")




	student_dict = metadata(hs_prefs, ms_prefs)
	n_6th = 1
	student_dict, prefs = sim6(n_6th, hs_prefs, ms_prefs, prefs)
	#prefs = pd.read_csv("with6th.csv")
	# prefs = prefs[-1*n_6th:] # just 6th graders


	# Resource Room students
	rr = pd.read_csv("~/Desktop/test_pref/resource_room.csv")

	# Get number of courses dictionary
	num_courses = get_num_courses(LP_input, hs_prefs, ms_prefs)

	r = Requirement(6, "People and Literature", "Inquiry and Tools")
	r2 = Requirement(9, 'African Studies', 'Latin American Literature')
	# mr = MiniRequirement(r)
	
	save_loc = "~/Desktop/gui_test" # this should be a folder
	O = Optimizer(prefs = prefs,
					LP_input = LP_input,
					teacher = teacher,
					GAP = .3,
					student_dict = student_dict,
					num_courses = num_courses,
					requirements = [r, r2],
					prox = prox,
					rr_df = rr,
					save_location = save_loc)

	# load the solution with rooms
	#at = "150/"
	#at = "test_100/"
	# O.XV = pickle.load(open(at+"xv.pkl", 'rb'))
	# O.CourseV = pickle.load(open(at+"coursev.pkl", 'rb'))
	# O.RoomV = pickle.load(open(at+"roomv.pkl", 'rb'))


	
	
	# re-index O.S just for the students real quick
	#O.S = range(n_6th)

	# Add constraints
	print("Adding Constraints")
	O.add_basic_constraints()
	O.add_max_constraint()
	#self.add_min_constraint()
	O.add_proximity_constraints()
	O.add_teacher_constraints()
	O.add_course_constraints()
	O.add_grade_level_requirements()
	O.add_room_constraints()
	O.add_rr_constraints()
	#O.add_period_constraints() # ONly if Other courses are in input
	print("Constraints Added")

	O.set_objective()
	#raise SystemExit	
	
	#--------------------
	#--------------------
	O.optimize()
	#--------------------
	#--------------------

	raise SystemExit


	

	# Save soltuions
	
	# pickle.dump(O.XV, open(save_loc+"/xv.pkl", 'wb'), pickle.HIGHEST_PROTOCOL)
	# pickle.dump(O.CourseV, open(save_loc+"/coursev.pkl", 'wb'), pickle.HIGHEST_PROTOCOL)
	# pickle.dump(O.RoomV, open(save_loc+"/roomv.pkl", 'wb'), pickle.HIGHEST_PROTOCOL)
	# pickle.dump(O.UV, open(save_loc+"/uv.pkl", 'wb'), pickle.HIGHEST_PROTOCOL)


	if not O.m.getStatus() == 'infeasible':
		O.assign_value_dicts()
	else:
		print("Not feasible soltuion")

	print("Pickling solutions")
	O.save_dicts()
	O.print_grid()
	#O.print_grid_no_room()
	O.print_all_student_schedules(rooms = True)
	O.diagnostic()

	#O.save_grid_no_rooms("test_grid_no_rooms.txt")
	O.save_grid()
	O.save_all_student_schedules(rooms=True, show_score=True)

	O.make_hist(save=True)
	O.plot_score_by_grade(save=True)

	# test solution
	S = Solution(Cd=O.Cd, 
				C= O.C,
				XV = O.XV,
				CourseV = O.CourseV,
				RoomV = O.RoomV,
				student_dict = O.student_dict,
				I_C_dict = O.I_C_dict,
				Ta = O.Ta,
				R = O.R,
				m = O.m,
				save_loc = "150_newpref/solution.pkl")
	S.save()


	# for i in O.S:
	# 	score = 0
	# 	for j in O.C:
	# 		score += O.P[i][j]*O.XV[i,j]
	# 	print("Student", i, ":", score)

# num_first = 0
# num_second = 0
# num_third = 0
# num_other = 0
# m = range(len(O.C) - 3)
# for i in O.S:
# 	for j in m:
# 		if (O.XV[i,j] == 1) and (O.P[i][j] == 3):
# 			num_first += 1
# 		elif (O.XV[i,j] == 1) and (O.P[i][j] == 2):
# 			num_second += 1
# 		elif (O.XV[i,j] == 1) and (O.P[i][j] == 1):
# 			num_third += 1
# 		elif (O.XV[i,j] == 1) and (O.P[i][j] == 0):
# 			# need to make sure not a double period second part
# 			d = 1
# 			try:
# 				d -= O.Db[j-1]
# 			except:
# 				pass
# 			num_other += d
# print("Number first choices given:", num_first)
# print("Number second choices given:", num_second)
# print("Number third choices given:", num_third)
# print("Number bad assignments:", num_other)

# def get_score(i):
# 	"""
# 	gets the score for a student index i
# 	"""
# 	s = 0
# 	for j in m:
# 		if O.XV[i,j] == 1:
# 			s += O.P[i][j]
# 	return s

# # # Make a histogram of scores
# scores = []
# for i in O.S:
# 	s = 0
# 	for j in m:
# 		if O.XV[i,j] == 1:
# 			s += O.P[i][j]
# 	scores.append(s)
# plt.hist(scores, bins=18)
# plt.title("Histogram of Student Scores")
# plt.xlabel("Score")
# plt.savefig(save_loc +"/score_hist.png", dpi=300)

# # Score by Grade plot
# sg = {}
# for g in [5,6,7,8,9,10,11,12]:
# 	sg[g] = []
# 	for i in O.S:
# 		if O.student_dict[i].grade == g:
# 			sg[g].append(get_score(i))

# for g in [5,6,7,8,9,10,11,12]:
# 	l = "Grade " + str(g)
# 	plt.scatter(g*np.ones(len(sg[g])), sg[g], label=l, alpha=.35)
# 	avg = np.mean(sg[g])
# 	plt.plot(g, avg, color="red", marker="_", ms=25)
# plt.xlabel("Grade")
# plt.ylabel("Score")
# plt.title("Scores by Grade")
#plt.savefig(save_loc + "/score_grade.png", dpi=400)



# 


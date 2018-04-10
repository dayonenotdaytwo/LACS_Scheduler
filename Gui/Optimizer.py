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

from Requirement import *

class Optimizer():
	"""
	Description

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

	def __init__(self, prefs, LP_input, grades, teacher, GAP, requirements=None,
			prox=None, save_location=None):
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
		self.Grades = None
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



		# main LP_input
		self.df = LP_input

		# Pulled from call
		self.teacher = teacher
		self.GAP = GAP
		self.requirements = requirements
		self.save_location = save_location

		# Clean up preferences (at least in current form)
		self.prefs = prefs.rename(columns={"Unnamed: 0": "Student"})

		# Place holders untill full data is made
		self.prox = pd.read_csv("../Resources/Proximity.csv")
		self.grades = pd.read_csv("../Resources/grades.csv", header=None)

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

		# Add Variables
		print("Adding Variables")
		self.add_variables()

		# Add constraints
		print("Adding Constraints")
		self.add_basic_constraints()
		self.add_proximity_constraints()
		self.add_teacher_constraints()
		self.add_course_constraints()
		self.add_grade_level_requirements()
		self.add_room_constraints()
		self.add_period_constraints()
		print("Constraints Added")

		self.set_objective()
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
		self.S = self.prefs["Student"].tolist() # list of all students (once we get ID make dictionary)

		# Courses
		self.Cd = {}
		for i in self.df.index:
			self.Cd[i] = self.df["Course Name"].iloc[i]

		self.C = range(len(self.Cd))

		# Gather "Other Indicies"
		self.other_indicies = []
		for j in self.Cd:
			if "Other" in self.Cd[j]:
				self.other_indicies.append(j)

		self.T = [1,2,3,4,7,8] # Periods

		# Instructors and corerspondence
		self.I = list(set(self.teacher[0]))

		# Grades for each student
		self.Grades = grades[1]

		# Extract Preferences
		self.P = self.prefs.drop("Student", axis=1).as_matrix()

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
		self.D = prox.drop("0", axis=1).as_matrix()

		# Create Proximity dictionary {subject:proximity vector}
		self.prox_dict = {}
		Subjects = list(self.prox.columns)[1:]
		for subj in list(self.prox.columns)[1:]:
			self.prox_dict[subj] = self.prox[subj]


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
				if self.teacher.iloc[index][0] == i:
					l = I_C_dict[i]
					l.append(self.teacher.iloc[index][1])
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
				"L6", "Sci A", "Sci B", "Sci C", "Music Room", "Gym", "Gym2"]

		# Department Courses
		Science_Rooms = ["Sci A", "Sci B", "Sci C"]
		Art_Rooms = ["Art"]
		Gym_Rooms = ["Gym", "Gym2"]
		Music_Rooms = ["Music Room"]
		Free_Rooms = list( set(R) - set(Science_Rooms + Art_Rooms + Gym_Rooms +
			Music_Rooms))

		# Get courses for each room type (Art, Science, Gym, Music, Resource)
		Art_Courses = self.df.index[self.df['Room Type'] == "Art"].tolist()
		Science_Courses = self.df.index[self.df['Room Type'] == "Science"].tolist()
		Gym_Courses = self.df.index[self.df['Room Type'] == "Gym"].tolist()
		Music_Courses = self.df.index[self.df['Room Type'] == "Music"].tolist()
		Resource_Courses = self.df.index[self.df['Room Type'] == "Resource"].tolist()

		room_constrained_subjects = ["Science", "Art", "Music", "Gym"]
		constrained_rooms = {"Science":Science_Rooms, "Art":Art_Rooms, 
			"Music":Music_Rooms, "Gym":Gym_Rooms}
		constrained_courses = {"Science":Science_Courses, "Art":Art_Courses,
			"Music":Music_Courses, "Gym":Gym_Courses}

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
		print("\tStudent/Course variable added")

		# Add Course Variable
		Course = {} # Variable dictionary
		for j in range(len(self.C)):
			for t in self.T:
				name = "Course " + str(j) + " in period " + str(t)
				# Course[j,t] = m.addVar(vtype=GRB.BINARY, name=name)
				Course[j,t] = self.m.addVar(vtype="B", name=name)
		print("\tCourse/Period variable added")

		# Create the u variable
		U = {}
		for i in self.S:
			for j in range(len(self.C)):
				for t in self.T:
					name = "min " + str(i) + ", " + str(j) + ", " + str(t)
					# U[i,j,t] = m.addVar(vtype=GRB.BINARY, name=name)
					U[i,j,t] = self.m.addVar(vtype="B", name=name)
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
		print("\tOne course per period")


		# "AND" Constraint--no more than one course per period for a student
		# Enforces the definition of the U variable
		for i in self.S:
			for j in self.C:
				# m.addConstr(X[i,j] == quicksum(U[i,j,t] for t in T))
				self.m.addCons(self.X[i,j] == quicksum(self.U[i,j,t] for t in self.T))
				for t in self.T:
					# m.addConstr(Course[j,t] >= U[i,j,t])
					self.m.addCons(self.Course[j,t] >= self.U[i,j,t])
		print("\tU set-up constraints (`and`) added")


		# Add capacity and minimum constraint
		for j in range(len(self.C)):
			self.m.addCons(quicksum(self.X[i,j] for i in self.S) <= self.MAX[j])
			self.m.addCons(quicksum(self.X[i,j] for i in self.S) >= self.MIN[j])
		print("\tCourse capacity")


	def add_proximity_constraints(self):
		"""
		Adds the proximity constraints
		"""
		print("\n\n\nTHE PROXIMITY CONSTRAINTS HAVE NOT BEEN IMPLEMENTED\n\n\n")
		pass 


	def add_teacher_constraints(self):
		"""
		Adds the teacher constraints:
			teacher teaches at most one course per period
		"""
		# Teacher teaching at most one course per period
		for k in range(len(self.I)):
			for t in self.T:
				# m.addConstr(quicksum(Course[j,t]*Ta[k][j] for j in C) <= 1)
				self.m.addCons(quicksum(self.Course[j,t]*self.Ta[k][j] 
						for j in self.C) <= 1)
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
		print("\tCourse taught only once")

		# Double period--consecutive constraints
		for j in range(len(self.C)):
			if self.Db[j] == 1: # if double period
				for t in self.T:
					if t != 4 and t != 8:
						# m.addConstr(Course[j,t] == Course[j+1, t+1]) # change to == from >= 
						self.m.addCons(self.Course[j,t] == self.Course[j+1, t+1]) # change to == from >= 
		print("\tDouble periods must be consecutive")


		# Double Period--not 4th or 8th
		for j in range(len(self.C)):
			if self.Db[j] == 1:
				# m.addConstr(Course[j,4] == 0)
				self.m.addCons(self.Course[j,4] == 0)
				# m.addConstr(Course[j,8] == 0)
				self.m.addCons(self.Course[j,8] == 0)
		print("\tDouble periods not in 4th or 8th")


		# # Double Period--Student in both
		for i in self.S:
			for j in range(len(self.C)):
				if self.Db[j] == 1:
					# m.addConstr(X[i,j+1] == X[i,j]) # this was >= but == is better?
					self.m.addCons(self.X[i,j+1] == self.X[i,j]) # this was >= but == is better?
		print("\tStudents in both parts of double")

		# Multi-Instance courses (students only in one instance--at most)
		for i in self.S:
			for course_set in self.multi_nested_list:
				# in at most one course of the list
				# m.addConstr(quicksum(X[i,j] for j in course_set) <= 1)
				self.m.addCons(quicksum(self.X[i,j] for j in course_set) <= 1)
		print("\tStudents in at most of instance of multi-instance Course ")



	def add_grade_level_requirements(self):
		"""
		Adds theg grade level requirements that are specified via the GUI
		"""
		print("\n\nSTILL NEED TO IMPLEMENT THE REQUIREMENT CONSTRAINTS\n\n")
		print("in this, we should think about forcing them in the first few")
		print("periods, or we could try to add that to the objective")
		pass


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
		print("\tCourses get one room")


		# Room gets at most one course per period
		for s in self.R:
			for t in self.T:
				# m.addConstr(quicksum(Rv[j,s,t] for j in c_mini) <= 1)
				self.m.addCons(quicksum(self.Rv[j,s,t] for j in self.c_mini) <= 1)
		print("\tRooms get at most one course per period")

		# Double periods in the same room
		for j in self.Cd:
			if self.Db[j] == 1:
				for t in self.T:
					if t != 4 and t != 8:
						for s in self.R:
							# m.addConstr(Rv[j,s,t] == Rv[j+1, s, t+1])
							self.m.addCons(self.Rv[j,s,t] == self.Rv[j+1, s, t+1])
		print("\tDouble Periods in same room")


		for subject in self.room_constrained_subjects:
			sub_courses = self.constrained_courses[subject] # coruses in this subject
			sub_rooms = self.constrained_rooms[subject] # appropriate rooms
			for j in sub_courses:
				for t in self.T:
					# m.addConstr(quicksum(Rv[j,s,t] for s in sub_rooms) == Course[j,t])
					self.m.addCons(quicksum(self.Rv[j,s,t] for s in sub_rooms)
						 == self.Course[j,t])
		print("\tCourses with subject specific room needs accomodated")


	def add_period_constraints(self):
		"""
		Adds the period constraints
			`other` in appropriate period
		"""
		# Force "Other" courses in specific periods
		for i in range(len(self.T)):
			# m.addConstr(Course[other_indicies[i], T[i]] == 1)
			self.m.addCons(self.Course[self.other_indicies[i], self.T[i]] == 1)
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
		print("GAP set")

		self.m.setObjective(-1*quicksum(self.X[i,j] for i in self.S 
			for j in self.other_indicies) + 
			quicksum(self.X[i,j]*self.P[i][j] for i in self.S 
			for j in self.C), "maximize")
		print("Objective Set")

	def optimize(self):
		"""
		Runs the optimization sequence
		"""
		print("-"*30 + "Optimization Starting" + "-"*30)
		self.m.optimize()




if __name__ == "__main__":
	"""
	Quick running tester
	"""

	# gets files
	LP_input = pd.read_csv("OptTestFiles/LP_input.csv")
	teacher = pd.read_csv("OptTestFiles/teacher.csv", header=None)
	prefs = pd.read_csv("OptTestFiles/prefs.csv")
	grades = pd.read_csv("OptTestFiles/grades.csv", header=None)
	prox =pd.read_csv("OptTestFiles/prox.csv")

	O = Optimizer(prefs, LP_input, grades, teacher, 1, None, prox, None)



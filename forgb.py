# forgb.py
# Kenneth Lipke
# Spring 2018
# LACS M.Eng Project

"""
Implmentation of our model in Gurobi
Pulls data from .csv files, organizes it into the appropriate dictionaries,
lists, and sets. Creates a Gurobi model, adds variables, constraints,
as well as an objective, then proceeds to solve. Finally, it produces various
outputs to judge preformance of the model
"""


#from pyscipopt import Model, quicksum
from gurobipy import *
import numpy as np
import pandas as pd
from os import system
import pickle 


## to run in interactive use: execfile("forgb.py")


# --------------------------------------------------------
# 						Read Data
# --------------------------------------------------------
prefs = pd.read_csv("Resources/FlatChoicesBinary.csv")
courses = pd.read_csv("Resources/FlatCourseSize.csv")
#prox = pd.read_csv("Resources/Proximity.csv")
prox = pd.read_csv("Resources/Proximity.csv")
teacher = pd.read_csv("Resources/Teacher_Info.csv", header=None)
course_rooms = pd.read_csv("Resources/CourseRoomReqs.csv")

# clean it up
prefs.rename(columns={"Unnamed: 0": "Student"}, inplace=True)
courses.rename(columns={"0":"Class"}, inplace=True)
courses.drop("Unnamed: 0", axis=1, inplace=True)


# --------------------------------------------------------
#					Pull out sets
# --------------------------------------------------------
# Extract sets
S = prefs["Student"].tolist() # list of all students (once we get ID make dictionary)

Cd = {} # Course dictionary
for i in courses.index:
    Cd[i] = courses["Class"].iloc[i]
C = range(len(Cd))
    
T = [1,2,3,4,7,8] # Periods

## Instructors and corerspondence
I = list(set(teacher[0]))
DW_courses = list(set(teacher[1]))

# Extract Preferences
P = prefs.drop("Student", axis=1).as_matrix()

# Double periods
Db = courses["Double"].fillna(0).astype(int)

# Course Sizes (min and max)
MIN = courses["Min"]
MAX = courses["Max"]

# To check feasibility:
#MIN = [3]*len(C)
#MAX = [100]*len(C)

# Proximity Matrix
D = prox.drop("0", axis=1).as_matrix()

# Create Proximity dictionary {subject:proximity vector}
prox_dict = {}
Subjects = list(prox.columns)[1:]
for subj in list(prox.columns)[1:]:
    prox_dict[subj] = prox[subj]

# --------------------------------------------------------
#					Map Teachers to Courses
# --------------------------------------------------------
# Need matrix with instructors as rows, all courses as columns, and 1 if teaching that course
I_C_dict = {}
for i in I:
    I_C_dict[i] = []
    for index in range(teacher.shape[0]):
        if teacher.iloc[index][0] == i:
            l = I_C_dict[i]
            l.append(teacher.iloc[index][1])
            I_C_dict[i] = l


# Teacher_Course_Matrix 
courses_list = list(Cd.values())
Teacher_Course_Matrix = np.zeros(len(courses_list))
for i in I:
    t = np.zeros(len(courses_list))
    for j in Cd:
        if Cd[j] in I_C_dict[i]:
            # print(i, "is teaching:", (40-len(i)-12)*".", Cd[j])
            t[j] =1
    Teacher_Course_Matrix = np.vstack([Teacher_Course_Matrix, np.matrix(t)])

Ta = np.array(Teacher_Course_Matrix[1:]) # matrix tying teachers to courses they teach


# --------------------------------------------------------
#					Set up Room Data
# --------------------------------------------------------
# Room Data (we will eventually need to tie this to subject, i.e. for science?)
#R = ["U1", "Steve", "U2", "U3", "U4/5", "U7", "U7", "L2", "L3", "Library", "Art", "L4", 
#        "L6", "Sci A", "Sci B", "Sci C", "Music Room", "Gym", "Gym2", "OtherRoom", "EmptyRoom"]
R = ["U1", "Steve", "U2", "U3", "U4/5", "U7", "U7", "L2", "L3", "Library", "Art", "L4", 
        "L6", "Sci A", "Sci B", "Sci C", "Music Room", "Gym", "Gym2"]


# Department Courses
Science_Rooms = ["Sci A", "Sci B", "Sci C"]
Art_Rooms = ["Art"]
Gym_Rooms = ["Gym", "Gym2"]
Music_Rooms = ["Music Room"]
Free_Rooms = list( set(R) - set(Science_Rooms + Art_Rooms + Gym_Rooms +
	Music_Rooms))

Science_Courses = course_rooms["Science"]
Art_Courses = course_rooms["Art"]
Gym_Courses = course_rooms["Gym"]
Music_Courses = course_rooms["Music"]
Free_Courses = course_rooms["Free"]
#Resource_Courses = course_rooms["Resource"]

room_constrained_subjects = ["Science", "Art", "Music", "Gym"]
constrained_rooms = {"Science":Science_Rooms, "Art":Art_Rooms, 
	"Music":Music_Rooms, "Gym":Gym_Rooms}
constrained_courses = {"Science":Science_Courses, "Art":Art_Courses,
	"Music":Music_Courses, "Gym":Gym_Courses}

#------------------------------------------------------------
#------------------------------------------------------------







#------------------------------------------------------------
#------------------------------------------------------------
#					Start Model Setup
#------------------------------------------------------------
#------------------------------------------------------------
# Create Model instance
m = Model("PhaseTwo")


# Trackers--to verify what SCIP/GB says
num_vars = 0
num_cons = 0


#------------------------------------------------------------
#						Create Variables
#------------------------------------------------------------
print "Adding variables"
# Add Student Variables (X)
X = {}
for i in S:
    for j in range(len(C)):
        name = "Student " + str(i) + " in course " + str(j)
        X[i,j] = m.addVar(vtype=GRB.BINARY, name=name)
        num_vars += 1
print "\tStudent/Course variable added"

# Add Course Variable
Course = {} # Variable dictionary
for j in range(len(C)):
    for t in T:
        name = "Course " + str(j) + " in period " + str(t)
        Course[j,t] = m.addVar(vtype=GRB.BINARY, name=name)
        num_vars += 1
print "\tCourse/Period variable added"

# Create the u variable
U = {}
for i in S:
    for j in range(len(C)):
        for t in T:
            name = "min " + str(i) + ", " + str(j) + ", " + str(t)
            U[i,j,t] = m.addVar(vtype=GRB.BINARY, name=name)
            num_vars += 1
print "\tU(Student/Course/Period) variable added"

# Define r  room variable (over course j in room r durring period t)
Rv = {}
for j in range(len(C)):
	if "Other" not in Cd[j] and "Empty" not in Cd[j]:
	    for s in R:
	        for t in T:
	            name = "Course " + str(j) + " in room " + str(s) + " durring period " + str(t)
	            Rv[j,s,t] = m.addVar(vtype=GRB.BINARY, name=name)
	            num_vars += 1
print "\tRoom/Period Variables added"

#------------------------------------------------------------
#------------------------------------------------------------
#						Add Constraints
#------------------------------------------------------------
#------------------------------------------------------------
print "Adding constraints"


# Force student in one course per period
for i in S:
    for t in T:
        m.addConstr(quicksum(U[i,j,t] for j in C) == 1) # one course per period
        num_cons += 1
print "\tOne course per period"


# "AND" Constraint--no more than one course per period for a student
for i in S:
    for j in C:
        m.addConstr(X[i,j] == quicksum(U[i,j,t] for t in T))
        num_cons += 1
        for t in T:
            m.addConstr(Course[j,t] >= U[i,j,t])
            num_cons += 1
print "\tU set-up constraints (`and`) added"


# must have preffed the course
for i in S:
	for j in Cd:
		m.addConstr(X[i,j] <= P[i][j])
		num_cons += 1
print "\tStudents in courses they prefer"


# Add capacity and minimum constraint
for j in range(len(C)):
    m.addConstr(quicksum(X[i,j] for i in S) <= MAX[j])
    #m.addConstr(quicksum(X[i,j] for i in S) <= 100)
    #m.addConstr(quicksum(X[i,j] for i in S) >= MIN[j])
    num_cons += 2
print "\tCourse capacity"



#------------------------------------------------------------
#					Proximity Constraints
#------------------------------------------------------------

# Setup proximity min and max dicts (temp untill we generate more granular data)
min_sub_dict = {}
max_sub_dict = {}
for subj in Subjects:
    min_sub_dict[subj] = np.ones(len(S))*0
    max_sub_dict[subj] = np.ones(len(S))*4


# # proximity by subject
for subject in Subjects:
    for i in S:
        if min_sub_dict[subject][i] > 0:
            m.addConstr(quicksum(prox_dict[subject][j]*X[i,j] for j in range(len(C))) >= min_sub_dict[subject][i])
        # do we always need a max?
        m.addConstr(quicksum(prox_dict[subject][j]*X[i,j] for j in range(len(C))) <= max_sub_dict[subject][i])
print "\tProximity constraint added"


#------------------------------------------------------------
#						Teacher Constraitns
#------------------------------------------------------------

# Teacher teaching at most one course per period
for k in range(len(I)):
    for t in T:
        m.addConstr(quicksum(Course[j,t]*Ta[k][j] for j in C) <= 1)
        num_cons += 1
print "\tTeacher teaches as most once per period"


#------------------------------------------------------------
#					Course Constraints
#------------------------------------------------------------
# Course Taught only once Constraint
for j in range(len(C)):
    m.addConstr(quicksum(Course[j,t] for t in T) == 1)
    num_cons += 1
print "\tCourse taught only once"

# Double period--consecutive constraints
for j in range(len(C)):
    if Db[j] == 1: # if double period
        for t in T:
            if t != 4 and t != 8:
                m.addConstr(Course[j,t] == Course[j+1, t+1]) # change to == from >= 
                num_cons += 1
print "\tDouble periods must be consecutive"


# # Double Period--not 4th or 8th
for j in range(len(C)):
    if Db[j] == 1:
        m.addConstr(Course[j,4] == 0)
        m.addConstr(Course[j,8] == 0)
        num_cons += 2
print "\tDouble periods not in 4th or 8th"


# # Double Period--Student in both
for i in S:
    for j in range(len(C)):
        if Db[j] == 1:
            m.addConstr(X[i,j+1] == X[i,j]) # this was >= but == is better?
            num_cons += 1
print "\tStudents in both parts of double"


#------------------------------------------------------------
#					Room Constraints
#------------------------------------------------------------
# If course taught, gets one room
for j in range(len(C)):
	if "Other" not in Cd[j] and "Empty" not in Cd[j]:
	    for t in T:
	        m.addConstr(quicksum(Rv[j,s,t] for s in R) == Course[j,t])
print "\tCourses get one room"

# make set of course indicies without Other and Empty
c_mini = []
for j in Cd:
	if "Other" not in Cd[j] and "Empty" not in Cd[j]:
		c_mini.append(j)

# Room gets at most one course per period
for s in R:
	for t in T:
		m.addConstr(quicksum(Rv[j,s,t] for j in c_mini) <= 1)
print "\tRooms get at most one course per period"

# Double periods in the same room
for j in Cd:
	if Db[j] == 1:
		for t in T:
			if t != 4 and t != 8:
				for s in R:
					m.addConstr(Rv[j,s,t] == Rv[j+1, s, t+1])
					num_cons += 1
print "\tDouble Periods in same room"

# force subject constrained courses into appropriate rooms
for subject in room_constrained_subjects:
	sub_courses = constrained_courses[subject] # coruses in this subject
	sub_rooms = constrained_rooms[subject] # appropriate rooms
	for j in Cd:
		if "Other" not in Cd[j] and "Empty" not in Cd[j]:
			if sub_courses[j] == 1: # if course is in subject
				for t in T:
					m.addConstr(quicksum(Rv[j,s,t] for s in sub_rooms) == Course[j,t])
print "\tCourses with subject specific room needs accomodated"


#-------------------------------------------------------------
#						`Other` Courses
#-------------------------------------------------------------
# Force "Other" courses in specific periods
other_indicies = []
for j in Cd:
    if "Other" in Cd[j]:
        other_indicies.append(j)
        
for i in range(len(T)):
    m.addConstr(Course[other_indicies[i], T[i]] == 1)
print "\t`Other` courses in each period"


print "All constraints added"




#-------------------------------------------------------------
#-------------------------------------------------------------
#						Set Objective
#-------------------------------------------------------------
#-------------------------------------------------------------
print "Setting objective"
m.setObjective(X[1,1]*0, GRB.MAXIMIZE) # just find a feasible solution

# try setting a gap
#m.MIPGap=.05 # 5% is good enough for me
#m.setObjective(quicksum(X[i,j]*P[i][j] for i in S for j in C), GRB.MAXIMIZE)


# print(str(num_vars), "Variables")
# print(str(num_cons), "Constraints")


#-------------------------------------------------------------
#							Solve
#-------------------------------------------------------------
# Solve model
print("-"*20 + "Optimization Starting" + "-"*20)
m.optimize() # NOTE: solver info printed to terminal




#------------------------------------------------------------
#------------------------------------------------------------
#
#					START RESULT DESCIRPTION
#
#------------------------------------------------------------
#------------------------------------------------------------

#------------------------------------------------------------
#						Helper Functions
#------------------------------------------------------------

def get_value(var):
	"""
	Takes in a variable instance, and returns its value
	"""
	# var_name = var.VarName
	# returned = m.getVarByName(var_name)
	# return returned.X
	return var.X

def get_enrollment(course):
	"""
	takes in a course index corrseponding to a course in Cd
	and returns the number of students enrolled
	Note: Assumes the variable value dictionaries have already been defined
	"""
	num_enrolled = 0
	for i in S:
		if XV[i,course] == 1:
			num_enrolled += 1
	return num_enrolled

def get_teacher(course):
	"""
	Takes in a course ID and retunrs the teachers name
	"""
	for k in range(len(I)):
		if Ta[k][course] == 1:
			return I[k]
	# if no teacher (other, or empty)
	return ""

def print_schedule(student):
	"""
	takes in the index of a student and prints out their schedule
	"""
	for t in T:
		for j in Cd:
			if XV[student,j] == 1 and CourseV[j,t] == 1:
				print "Period " + str(t) + ": " + Cd[j]

#-------------------------------------------------------------
#						Save Variable Values
#-------------------------------------------------------------
# Save all variable values
XV = {}
CourseV = {}
for i in S:
	for j in range(len(C)):
		# get student variable
		XV[i,j] = get_value(X[i,j])
		for t in T:
			CourseV[j,t] = get_value(Course[j,t])
# get rooms
RoomV = {}
# for j in range(len(C)):
for j in c_mini:
	for s in R:
		for t in T:
			RoomV[j,s,t] = get_value(Rv[j,s,t])
			#RoomV[j,s,t] = Rv[j,s,t].X

UV = {}
for i in S:
	for j in Cd:
		for t in T:
			UV[i,j,t] = get_value(U[i,j,t])


#-------------------------------------------------------------
#						Optional Pickling 
#-------------------------------------------------------------
# pickle those dictionaries with the values
# with open('Xvals.pickle', 'wb') as handle:
#     pickle.dump(XV, handle, protocol=pickle.HIGHEST_PROTOCOL)

# with open('RoomVals.pickle', 'wb') as handle:
#     pickle.dump(RoomV, handle, protocol=pickle.HIGHEST_PROTOCOL)

# with open('UVals.pickle', 'wb') as handle:
#     pickle.dump(UV, handle, protocol=pickle.HIGHEST_PROTOCOL)


#-------------------------------------------------------------
#					Courses by Period
#-------------------------------------------------------------
# By just period
print "\n\n"
for t in T:
	print "PERIOD " + str(t) + " " + "-"*30
	for j in range(len(C)):
		if CourseV[j,t] ==1 :
			print Cd[j]
	print "\n"


#-------------------------------------------------------------
#						Detailed Grid Listing
#-------------------------------------------------------------
print "\n\n"
for t in T:
	print "-"*20 + " " + "PERIOD " + str(t) + " " + "-"*110
	print "Room" + 36*" " + "Course" + 34*" " + "Enrollment" + " "*(40 - len("Enrollment")) + "Teacher"
	print "-"*140
	# for j in range(len(C)):
	for j in c_mini:
		# if the course is offered
		if CourseV[j,t] == 1:
			# figure out which room
			for s in R:
				if RoomV[j,s,t] == 1:
					num_enrolled = get_enrollment(j)
					print s + (40 - len(s))*"." + Cd[j] + (40 - len(Cd[j]))*"." \
						+ str(num_enrolled) + "."*(40 - len(str(num_enrolled))) + get_teacher(j)
	print "\n"



#-------------------------------------------------------------
#					Enrollment by Course
#-------------------------------------------------------------
# Get enrollment totals:
print "\n\n"
print "Course " + (40 -len("Course"))*" " + " Enrolled"
print "-"*50
for j in Cd:
    num = 0
    for i in S:
        if XV[i,j] == 1:
            num += 1
    print Cd[j] + (40 - len(Cd[j]))*"." + str(num)


#------------------------------------------------------------
#					Teachers by Period
#------------------------------------------------------------
# Print teachers by period (to ensure no doubles)
teacher_list = list(I_C_dict.keys())
for t in T:
    print "PERIOD " + str(t) + " " + "-"*30
    for j in Cd:
        if CourseV[j,t]==1:
            for k in range(len(I)):
                if Ta[k][j] == 1:
                    print I[k]
    print "\n"     



#------------------------------------------------------------
#				Show all Student Schedules
#------------------------------------------------------------
# print all schedules
# for i in S:
# 	print "Student " + str(i)
# 	print_schedule(i)
# 	print "\n"


#------------------------------------------------------------
#				Model Preformance Stats
#------------------------------------------------------------
# figure out how many students didn't get a class they preffed:
num_disliked = 0
num_liked = 0
for i in S:
	for j in Cd:
		if XV[i,j] != P[i][j]:
			num_disliked += 1
		if XV[i,j] == 1 and P[i][j] == 1:
			num_liked += 1

print "Number of dispreffered courses assigned: " + str(num_disliked)
print "Number of preffered courses assigned: " + str(num_liked)

# count number of courses each student is in, show min and max
min_courses = 1000
max_courses = 0
for i in S:
	num_courses = 0
	for j in Cd:
		num_courses += XV[i,j]
	min_courses = np.min([num_courses, min_courses])
	max_courses = np.max([num_courses, max_courses])

print "Min Enrollment: " + str(min_courses)
print "Max Enrollment: " + str(max_courses)








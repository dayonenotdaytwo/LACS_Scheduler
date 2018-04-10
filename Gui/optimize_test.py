# optimize_test.py
# Kenneth Lipke

# Script version of opmimize_schedule function for debugging


from pyscipopt import Model, quicksum
# from gurobipy import *
import numpy as np
import pandas as pd
from os import system
import pickle 
import timeit # just to check setuptie

from Requirement import *

#prefs = pd.read_csv("../Resources/FlatChoicesBinary.csv")
prefs = pd.read_csv("OptTestFiles/prefs.csv")
# LP_input = pd.read_csv("../Resources/Refactored_Files/LP_Input.csv")
LP_input = pd.read_csv("OptTestFiles/LP_input.csv")
grades = None
teacher = pd.read_csv("OptTestFiles/teacher.csv", header=None)
GAP = .5


# def optimize_schedule(prefs, LP_input, grades, teacher, GAP, requirements=None,
# 			prox=None, save_location=None):
"""
Runs the optimizer in SCIP

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
				   these are then iterated over, parsed, and coded


NOTE: most of the commented out stuff is from a previous iteration
where the data was being pulled from various .csv files, I have included
it as a helper if we need to go back and de-bug and see how it once worked
when the data was coming from somewhere else

NOTE 2: The commented out variables, constraints, and other optimization
code is for Gurobi, the non-commented is for SCIP
"""


start_time = timeit.default_timer()

# --------------------------------------------------------
# 						Read Data
# --------------------------------------------------------
# prefs = pd.read_csv("Resources/FlatChoicesBinary.csv")
# courses = pd.read_csv("Resources/FlatCourseSize.csv")
#prox = pd.read_csv("Resources/Proximity.csv")
prox = pd.read_csv("../Resources/Proximity.csv")
#teacher = pd.read_csv("../Resources/Teacher_Info.csv", header=None)
# course_rooms = pd.read_csv("Resources/CourseRoomReqs.csv")
grades = pd.read_csv("../Resources/grades.csv", header=None)

# clean it up
prefs.rename(columns={"Unnamed: 0": "Student"}, inplace=True)
# courses.rename(columns={"0":"Class"}, inplace=True)
# courses.drop("Unnamed: 0", axis=1, inplace=True)

# NEW DATA
#df = pd.read_csv("Resources/LP_Input.csv")
df = LP_input


# --------------------------------------------------------
#					Pull out sets
# --------------------------------------------------------
# Extract sets
S = prefs["Student"].tolist() # list of all students (once we get ID make dictionary)

# Cd = {} # Course dictionary
# for i in courses.index:
#     Cd[i] = courses["Class"].iloc[i]
Cd = {}
for i in df.index:
	Cd[i] = df["Course Name"].iloc[i]

C = range(len(Cd))

# Gather "Other Indicies"
other_indicies = []
for j in Cd:
    if "Other" in Cd[j]:
        other_indicies.append(j)

T = [1,2,3,4,7,8] # Periods

## Instructors and corerspondence
I = list(set(teacher[0]))
DW_courses = list(set(teacher[1]))

# Grades for each student
Grades = grades[1]

# Extract Preferences
P = prefs.drop("Student", axis=1).as_matrix()

# Double periods
# Db = courses["Double"].fillna(0).astype(int)
Db = df["Double Period"].fillna(0).astype(int)

# Course Sizes (min and max)
# MIN = courses["Min"]
# MAX = courses["Max"]
MIN = df["Min"]
MAX = df["Max"]

# To check feasibility:
# MIN = [3]*len(C)
# MAX = [40]*len(C)

# Proximity Matrix
D = prox.drop("0", axis=1).as_matrix()

# Create Proximity dictionary {subject:proximity vector}
prox_dict = {}
Subjects = list(prox.columns)[1:]
for subj in list(prox.columns)[1:]:
    prox_dict[subj] = prox[subj]

# Required Courses
grade_requirements = {}
for grade in [5,6,7,8,9,10,11,12]:
	grade_requirements[grade] = df.index[df['Required Grades'] == grade].tolist()


## COMMENTED OUT ONLY BECAUSE WILL HAVE TO TOTALLY OVERHAUL LATER,
## WITH THE USER INPUTTED REQUIREMENTS
# remove empties
# for g in grade_requirements.keys():
# 	if grade_requirements[g] == []:
# 		del grade_requirements[g]

# --------------------------------------------------------
#                  Multi-Instance Course list
# -------------------------------------------------------- 
# Look through input to determine which courses are multi-input
# Create a list of these courses (only the first half of the double
# if it is a double course)
multi = df["Number of Instances"].fillna(0).astype(int)
multi_nested_list = []
#raise ValueError("I want to stop here")
j = 0
while j < len(Cd):
    # if it is part of multi-instance cluster
    if multi[j] == 2:
        # if it is a double period
        if Db[j] == 1:
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


# ignore OTHER in multi-instance (these have 6 next to them)


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

# Science_Courses = course_rooms["Science"]
# Art_Courses = course_rooms["Art"]
# Gym_Courses = course_rooms["Gym"]
# Music_Courses = course_rooms["Music"]
# Free_Courses = course_rooms["Free"]
#Resource_Courses = course_rooms["Resource"]

# Get courses for each room type (Art, Science, Gym, Music, Resource)
Art_Courses = df.index[df['Room Type'] == "Art"].tolist()
Science_Courses = df.index[df['Room Type'] == "Science"].tolist()
Gym_Courses = df.index[df['Room Type'] == "Gym"].tolist()
Music_Courses = df.index[df['Room Type'] == "Music"].tolist()
Resource_Courses = df.index[df['Room Type'] == "Resource"].tolist()

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
m = Model("Schedule")


# Trackers--to verify what SCIP/GB says
num_vars = 0
num_cons = 0


#------------------------------------------------------------
#						Create Variables
#------------------------------------------------------------
print("Adding variables")
# Add Student Variables (X)
X = {}
for i in S:
    for j in range(len(C)):
        name = "Student " + str(i) + " in course " + str(j)
        # X[i,j] = m.addVar(vtype=GRB.BINARY, name=name)
        X[i,j] = m.addVar(vtype="B", name=name)
        num_vars += 1
print("\tStudent/Course variable added")

# Add Course Variable
Course = {} # Variable dictionary
for j in range(len(C)):
    for t in T:
        name = "Course " + str(j) + " in period " + str(t)
        # Course[j,t] = m.addVar(vtype=GRB.BINARY, name=name)
        Course[j,t] = m.addVar(vtype="B", name=name)
        num_vars += 1
print("\tCourse/Period variable added")

# Create the u variable
U = {}
for i in S:
    for j in range(len(C)):
        for t in T:
            name = "min " + str(i) + ", " + str(j) + ", " + str(t)
            # U[i,j,t] = m.addVar(vtype=GRB.BINARY, name=name)
            U[i,j,t] = m.addVar(vtype="B", name=name)
            num_vars += 1
print("\tU(Student/Course/Period) variable added")

# Define r  room variable (over course j in room r durring period t)
Rv = {}
for j in range(len(C)):
	if "Other" not in Cd[j] and "Empty" not in Cd[j]:
	    for s in R:
	        for t in T:
	            name = "Course " + str(j) + " in room " + str(s) + \
	            		" durring period " + str(t)
	            # Rv[j,s,t] = m.addVar(vtype=GRB.BINARY, name=name)
	            Rv[j,s,t] = m.addVar(vtype="B", name=name)
	            num_vars += 1
print("\tRoom/Period Variables added")

#------------------------------------------------------------
#------------------------------------------------------------
#						Add Constraints
#------------------------------------------------------------
#------------------------------------------------------------
print("Adding constraints")


# Force student in one course per period
for i in S:
    for t in T:
        # m.addConstr(quicksum(U[i,j,t] for j in C) == 1) # one course per period
        m.addCons(quicksum(U[i,j,t] for j in C) == 1) # one course per period
        num_cons += 1
print("\tOne course per period")


# "AND" Constraint--no more than one course per period for a student
for i in S:
    for j in C:
        # m.addConstr(X[i,j] == quicksum(U[i,j,t] for t in T))
        m.addCons(X[i,j] == quicksum(U[i,j,t] for t in T))
        num_cons += 1
        for t in T:
            # m.addConstr(Course[j,t] >= U[i,j,t])
            m.addCons(Course[j,t] >= U[i,j,t])
            num_cons += 1
print("\tU set-up constraints (`and`) added")


# must have preffed the course (minus the requirements)
# 8th graders must be in Researchers (j=88)
# 9th Graders in 1 of African Studies (8), or Latrin American Studies (61)
# 6th Graders in People and Lit (78,80), or Inquiry and Tools (52,54)
for i in S:
	for j in Cd:
		if Grades[i] == 8 and j == 88:
			pass
		elif Grades[i] == 9 and (j in [8,9,61,62]):
			pass
		elif Grades[i] == 6 and (j in [78,79,80,81, 52,53,54,55]):
			# so many as these are alternates and doubles
			pass
		else:
			# m.addConstr(X[i,j] <= P[i][j])
			m.addCons(X[i,j] <= P[i][j])
			num_cons += 1
print("\tStudents in courses they prefer" )

# g = 0
# for i in S:
# 	if Grades[i] == 9:
# 		if P[i][8] == 1:
# 			g += 1



# Add capacity and minimum constraint
for j in range(len(C)):
    # m.addConstr(quicksum(X[i,j] for i in S) <= MAX[j])
    m.addCons(quicksum(X[i,j] for i in S) <= MAX[j])
    #m.addConstr(quicksum(X[i,j] for i in S) <= 100)
    #m.addConstr(quicksum(X[i,j] for i in S) >= MIN[j])
    m.addCons(quicksum(X[i,j] for i in S) >= MIN[j])
    num_cons += 2
print("\tCourse capacity")



#------------------------------------------------------------
#					Proximity Constraints
#------------------------------------------------------------

# Setup proximity min and max dicts (temp untill we generate more granular data)
min_sub_dict = {}
max_sub_dict = {}
for subject in Subjects:
    min_sub_dict[subject] = np.ones(len(S))*0
    max_sub_dict[subject] = np.ones(len(S))*3 
    # it works when max is 6 --> I think the constraints are written correctly?
    # infeasible when 5, very suspicious


# # proximity by subject
#for subject in Subjects:
for subject in ["K", "F", "D", "M", "IIC", "VI", "C", "IV", "IIA", "E", "I",
			"H", "V", "VII", "Other", "G", "J", "IIB", "L", "IB"]: # test with limited set of subjects, trying to find issue
	for i in S:
	    if min_sub_dict[subject][i] > 0:
	        # m.addConstr(quicksum(prox_dict[subject][j]*X[i,j] for j in range(len(C))) >= min_sub_dict[subject][i])
	        m.addCons(quicksum(prox_dict[subject][j]*X[i,j] for j in range(len(C))) >= min_sub_dict[subject][i])
	    # do we always need a max?
	    # m.addConstr(quicksum(prox_dict[subject][j]*X[i,j] for j in range(len(C))) <= max_sub_dict[subject][i])
	    m.addCons(quicksum(prox_dict[subject][j]*X[i,j] for j in range(len(C))) <= max_sub_dict[subject][i])
print("\tProximity constraint added")


#------------------------------------------------------------
#						Teacher Constraitns
#------------------------------------------------------------



# Teacher teaching at most one course per period
for k in range(len(I)):
    for t in T:
        # m.addConstr(quicksum(Course[j,t]*Ta[k][j] for j in C) <= 1)
        m.addCons(quicksum(Course[j,t]*Ta[k][j] for j in C) <= 1)
        num_cons += 1
print("\tTeacher teaches as most once per period")


#------------------------------------------------------------
#					Course Constraints
#------------------------------------------------------------
# Course Taught only once Constraint
for j in range(len(C)):
    # m.addConstr(quicksum(Course[j,t] for t in T) == 1)
    m.addCons(quicksum(Course[j,t] for t in T) == 1)
    num_cons += 1
print("\tCourse taught only once")

# Double period--consecutive constraints
for j in range(len(C)):
    if Db[j] == 1: # if double period
        for t in T:
            if t != 4 and t != 8:
                # m.addConstr(Course[j,t] == Course[j+1, t+1]) # change to == from >= 
                m.addCons(Course[j,t] == Course[j+1, t+1]) # change to == from >= 
                num_cons += 1
print("\tDouble periods must be consecutive")


# # Double Period--not 4th or 8th
for j in range(len(C)):
    if Db[j] == 1:
        # m.addConstr(Course[j,4] == 0)
        m.addCons(Course[j,4] == 0)
        # m.addConstr(Course[j,8] == 0)
        m.addCons(Course[j,8] == 0)
        num_cons += 2
print("\tDouble periods not in 4th or 8th")


# # Double Period--Student in both
for i in S:
    for j in range(len(C)):
        if Db[j] == 1:
            # m.addConstr(X[i,j+1] == X[i,j]) # this was >= but == is better?
            m.addCons(X[i,j+1] == X[i,j]) # this was >= but == is better?
            num_cons += 1
print("\tStudents in both parts of double")

# Multi-Instance courses (students only in one instance--at most)
for i in S:
    for course_set in multi_nested_list:
        # in at most one course of the list
        # m.addConstr(quicksum(X[i,j] for j in course_set) <= 1)
        m.addCons(quicksum(X[i,j] for j in course_set) <= 1)
print("\t Students in at most of instance of multi-instance Course ")




#------------------------------------------------------------
#					Required Courses
#------------------------------------------------------------
# 8th graders must be in Researchers (j=88)
# 9th Graders in 1 of African Studies (8), or Latrin American Studies (61)
# 6th Graders in People and Lit (78,80), or Inquiry and Tools (52,54)


# MUST RE-IMPLEMENT THIS BASED ON THE REAUIREMENT SOLICIATIONS
# for i in S:
# 	if Grades[i] == 8:
# 		m.addConstr(X[i,88] == 1)
# 	if Grades[i] == 9:
# 		m.addConstr(X[i,8] + X[i,61] == 1)
# 	if Grades[i] == 6:
# 		m.addConstr(X[i,78] + X[i,80] + X[i,52] + X[i,54] == 1)
# print "\tGrade level course requirements"

print("\n\n\n FIGURE OUT HOW TO CODE IN THE REQUIREMENTS \n\n\n\n")

# for i in S:
# 	# For each grade that has some requirement
# 	for grade in grade_requirements.keys():
# 		# Determine if this student a restricted grade
# 		if Grades[i] == grade:
# 			for i in range(len(grade_requirements[grade])):
# 				j = grade_requirements[grade][i] # pull course index 
# 				# Determine if multi-instance
# 				if multi[j] != 0:
# 					# If also double
# 					if Db[j] == 1:
## INCOMPLETE:
# I am thinking about how to handle this with 6th grades who have OR conditions




#------------------------------------------------------------
#					Room Constraints
#------------------------------------------------------------
# If course taught, gets one room
for j in range(len(C)):
	if "Other" not in Cd[j] and "Empty" not in Cd[j]:
	    for t in T:
	        # m.addConstr(quicksum(Rv[j,s,t] for s in R) == Course[j,t])
	        m.addCons(quicksum(Rv[j,s,t] for s in R) == Course[j,t])
print("\tCourses get one room")

# make set of course indicies without Other and Empty
c_mini = []
for j in Cd:
	if "Other" not in Cd[j] and "Empty" not in Cd[j]:
		c_mini.append(j)

# Room gets at most one course per period
for s in R:
	for t in T:
		# m.addConstr(quicksum(Rv[j,s,t] for j in c_mini) <= 1)
		m.addCons(quicksum(Rv[j,s,t] for j in c_mini) <= 1)
print("\tRooms get at most one course per period")

# Double periods in the same room
for j in Cd:
	if Db[j] == 1:
		for t in T:
			if t != 4 and t != 8:
				for s in R:
					# m.addConstr(Rv[j,s,t] == Rv[j+1, s, t+1])
					m.addCons(Rv[j,s,t] == Rv[j+1, s, t+1])
					num_cons += 1
print("\tDouble Periods in same room")

# force subject constrained courses into appropriate rooms
# for subject in room_constrained_subjects:
# 	sub_courses = constrained_courses[subject] # coruses in this subject
# 	sub_rooms = constrained_rooms[subject] # appropriate rooms
# 	for j in Cd:
# 		if "Other" not in Cd[j] and "Empty" not in Cd[j]:
# 			if sub_courses[j] == 1: # if course is in subject
# 				for t in T:
# 					m.addConstr(quicksum(Rv[j,s,t] for s in sub_rooms) == Course[j,t])
# print "\tCourses with subject specific room needs accomodated"

for subject in room_constrained_subjects:
	sub_courses = constrained_courses[subject] # coruses in this subject
	sub_rooms = constrained_rooms[subject] # appropriate rooms
	for j in sub_courses:
		for t in T:
			# m.addConstr(quicksum(Rv[j,s,t] for s in sub_rooms) == Course[j,t])
			m.addCons(quicksum(Rv[j,s,t] for s in sub_rooms) == Course[j,t])
print("\tCourses with subject specific room needs accomodated")


#-------------------------------------------------------------
#						Period Constraints
#-------------------------------------------------------------
# Force "Other" courses in specific periods
for i in range(len(T)):
    # m.addConstr(Course[other_indicies[i], T[i]] == 1)
    m.addCons(Course[other_indicies[i], T[i]] == 1)
print("\t`Other` courses in each period")


# Required Courses in periods 1-4
# Must be in begning of day 
# for j in [88, 8, 9, 61, 62, 78, 79, 80, 81, 52, 53, 54, 55]:
# #for j in [88, 8, 9, 61, 62]:
# 	# m.addConstr(quicksum(Course[j, t] for t in [1,2,3,4]) == 1)
# 	m.addCons(quicksum(Course[j, t] for t in [1,2,3,4]) == 1)
# print "\tRequired courses in periods 1 -> 4"

# # Concurrance  (People and lit (78,80)) and (Inquire and tools (52, 54))
# for t in T:
# 	#m.addConstr(Course[78,t] == Course[80,t]) # ISSUE! <-----------------------------
# 	m.addConstr(Course[52,t] == Course[54,t])
# print "Concurrance of Multi-instance courses"

print("TODO: MAKE SURE THE REAUIRED DOUBLE PERIOD COURSES IN MORNING?")





print("All constraints added")






#-------------------------------------------------------------
#-------------------------------------------------------------
#						Set Objective
#-------------------------------------------------------------
#-------------------------------------------------------------

# Null objective
# m.setObjective(X[1,1]*0, GRB.MAXIMIZE) # just find a feasible solution

# Set Gap
# m.Params.MIPGap=.3 # 30% <-- I know this is appropriate as have run quite a bit
# m.Params.MIPGap=1
m.setRealParam('limits/gap', GAP)
print("GAP set")

# Preference objective
#m.setObjective(quicksum(X[i,j]*P[i][j] for i in S for j in C), GRB.MAXIMIZE)

# Minimize other objective
# m.setObjective(-1*quicksum(X[i,j] for i in S for j in other_indicies), GRB.MAXIMIZE)

# Minimize other, and Maximize Prefs
m.setObjective(-1*quicksum(X[i,j] for i in S for j in other_indicies) + 
	quicksum(X[i,j]*P[i][j] for i in S for j in C), "maximize")


print("Objective Set")


# print(str(num_vars), "Variables")
# print(str(num_cons), "Constraints")




elapsed = timeit.default_timer() - start_time
print("Model setup in " + str(round(elapsed,3)) + " seconds")
#-------------------------------------------------------------
#							Solve
#-------------------------------------------------------------
# Solve model
print("-"*30 + "Optimization Starting" + "-"*30)
m.optimize() # NOTE: solver info printed to terminal


# What am I going to do with the solution?
# Maybe make a solution object, that saves the variable values, along
# with the courses, teacher names, etc. this can easily be pickled,
# and parsed to get the schedules?

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


# Create Solution object to faving
solution = Solution(Cd, R, Ta, S, XV, CourseV, RoomV, UV)

# Save the solution 
file = save_location + ".pkl"
with open(file, "rb") as output:
	pickle.dump(solution, output, pickle.HIGHEST_PROTOCOL)

# Return to solution object as well
# return solution



def get_value(model, var):
	"""
	Takes in a model and a variable for that model
	returns the binary value of the variable
	take into account the even for SCIP "binary" variables
	the results may not be exactly 0 or 1
	"""

	scip_val = model.getVal(var)
	if scip_val > 0.75:
		return 1
	else:
		return 0


# if __name__ == "__main__":

	# prefs = pd.read_csv("../Resources/FlatChoicesBinary.csv")
	# LP_input = pd.read_csv("../Resources/Refactored_Files/LP_Input.csv")
	# grades = None
	# teacher = pd.read_csv("../Resources/Teacher_Info.csv", header=None)
	# GAP = .5
# 	optimize_schedule(prefs, LP_input, grades, teacher, GAP, requirements=None,
# 			prox=None, save_location=None)




"""
Changes you had to make:
- teacher file has to have no header

"""










#from pyscipopt import Model, quicksum
from gurobipy import *
import numpy as np
import pandas as pd
from os import system


## to run in interactive use: execfile("forgb.py")


# read in data
prefs = pd.read_csv("Resources/FlatChoicesBinary.csv")
courses = pd.read_csv("Resources/FlatCourseSize.csv")
#prox = pd.read_csv("Resources/Proximity.csv")
prox = pd.read_csv("Resources/Proximity.csv")
teacher = pd.read_csv("Resources/Teacher_Info.csv", header=None)

# clean it up
prefs.rename(columns={"Unnamed: 0": "Student"}, inplace=True)
courses.rename(columns={"0":"Class"}, inplace=True)
courses.drop("Unnamed: 0", axis=1, inplace=True)



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



# Room Data (we will eventually need to tie this to subject, i.e. for science?)
R = ["U1", "Steve", "U2", "U3", "U4/5", "U7", "U7", "L2", "L3", "Library", "Art", "L4", 
        "L6", "Sci A", "Sci B", "Sci C", "Music Room", "Gym", "Gym2", "OtherRoom", "EmptyRoom"]
# Test with way more rooms
# R = []
# for i in range(500):
#     R.append("R" + str(i))


# Extract Preferences
P = prefs.drop("Student", axis=1).as_matrix()
#P = np.ones([len(S),len(C)]) # all 1's as test (student will take any course)


# Double periods
Db = courses["Double"].fillna(0).astype(int)



# Proximity Matrix
D = prox.drop("0", axis=1).as_matrix()




# Create Proximity dictionary {subject:proximity vector}
prox_dict = {}
Subjects = list(prox.columns)[1:]
for subj in list(prox.columns)[1:]:
    prox_dict[subj] = prox[subj]



# Course Sizes (min and max)
MIN = courses["Min"]
MAX = courses["Max"]

# To check feasibility:
#MIN = [0]*len(C)
#MAX = [100]*len(C)



# Setup model
m = Model("PhaseTwo")


# Trackers--to verify what SCIP says
num_vars = 0
num_cons = 0


# In[13]:

print "adding variables"
# Add Student Variables (X)
X = {}
for i in S:
    for j in range(len(C)):
        name = "Student " + str(i) + " in course " + str(j)
        #X[i,j] = m.addVar(name, vtype=GRB.BINARY)
        X[i,j] = m.addVar(vtype=GRB.BINARY, name=name)
        num_vars += 1




# Add Course Variable
Course = {} # Variable dictionary
for j in range(len(C)):
    for t in T:
        name = "Course " + str(j) + " in period " + str(t)
        #Course[j,t] = m.addVar(name, vtype=GRB.BINARY)
        Course[j,t] = m.addVar(vtype=GRB.BINARY, name=name)
        num_vars += 1



# Create the u variable
U = {}
for i in S:
    for j in range(len(C)):
        for t in T:
            name = "min " + str(i) + ", " + str(j) + ", " + str(t)
            U[i,j,t] = m.addVar(vtype=GRB.BINARY, name=name)
            num_vars += 1




print "adding constraints"

# Force student in one course per period
for i in S:
    for t in T:
        m.addConstr(quicksum(U[i,j,t] for j in C) == 1) # one course per period
        num_cons += 1




# "AND" Constraint--no more than one course per period for a student
for i in S:
    for j in C:
        m.addConstr(X[i,j] == quicksum(U[i,j,t] for t in T))
        num_cons += 1
        for t in T:
            m.addConstr(Course[j,t] >= U[i,j,t])
            num_cons += 1

print "\tAND constraint added"



# Add capacity and minimum constraint
for j in range(len(C)):
    m.addConstr(quicksum(X[i,j] for i in S) <= MAX[j])
    #m.addConstr(quicksum(X[i,j] for i in S) <= 100)
    #m.addCons(quicksum(X[i,j] for i in S) >= 0)
    num_cons += 2




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
# Teacher teaching at most one course per period
for k in range(len(I)):
    for t in T:
        m.addConstr(quicksum(Course[j,t]*Ta[k][j] for j in C) <= 1)
        num_cons += 1




# Course Taught only once Constraint
for j in range(len(C)):
    m.addConstr(quicksum(Course[j,t] for t in T) == 1)
    num_cons += 1




# Double period--consecutive constraints
for j in range(len(C)):
    if Db[j] == 1: # if double period
        for t in T:
            if t != 4 and t != 8:
                m.addConstr(Course[j,t] == Course[j+1, t+1]) # change to == from >= 
                num_cons += 1



# # Double Period--not 4th or 8th
for j in range(len(C)):
    if Db[j] == 1:
        m.addConstr(Course[j,4] == 0)
        m.addConstr(Course[j,8] == 0)
        num_cons += 2



# # Double Period--Student in both
for i in S:
    for j in range(len(C)):
        if Db[j] == 1:
            m.addConstr(X[i,j+1] == X[i,j]) # this was >= but == is better?
            num_cons += 1

print "\tDouble period constraint added"

print "\tWorking on Room constraints"
# Define r  room variable (over course j in room r durring period t)
Rv = {}
for j in range(len(C)):
    for s in R:
        for t in T:
            name = "Course " + str(j) + " in room " + str(s) + " durring period " + str(t)
            Rv[j,s,t] = m.addVar(vtype=GRB.BINARY, name=name)
            num_vars += 1
print "Room Variables added"


# If course taught, gets one room
print R
for j in range(len(C)):
    for t in T:
        m.addConstr(quicksum(Rv[j,s,t] for s in R) == Course[j,t])

## -------------	NEW CONSTRAINT (IS NEEDED) -----------------
# Room gets at most one course per period
for s in R:
	for t in T:
		m.addConstr(quicksum(Rv[j,s,t] for j in range(len(Cd))) <= 1)
# --------------------------------------------------------------

## -----------------------	test -----------------------------
# course gets at most one room per period
# for j in Cd:
# 	for t in T:
# 		m.addConstr(quicksum(Rv[j,s,t] for s in R) <= 1)
#-------------------------------------------------------------

# # Force "Other" courses in specific periods
other_indicies = []
for j in Cd:
    if "Other" in Cd[j]:
        other_indicies.append(j)
        
for i in range(len(T)):
    m.addConstr(Course[other_indicies[i], T[i]] == 1)


# Set objective
#m.setObjective(quicksum(X[i,j]*P[i][j] for i in S for j in C), "maximize")
print "Setting objective"
m.setObjective(X[1,1]*0, GRB.MAXIMIZE) # just find a feasible solution





print(str(num_vars), "Variables")
print(str(num_cons), "Constraints")





# Solve model
print("-"*20 + "Optimization Starting" + "-"*20)
m.optimize() # NOTE: solver info printed to terminal


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
for j in range(len(C)):
	for s in R:
		for t in T:
			RoomV[j,s,t] = get_value(Rv[j,s,t])
			#RoomV[j,s,t] = Rv[j,s,t].X


# By just period
print "\n\n"
for t in T:
	print "PERIOD " + str(t) + " " + "-"*30
	for j in range(len(C)):
		if CourseV[j,t] ==1 :
			print Cd[j]
	print "\n"


# By period and Room
print "\n\n"
for t in T:
	print "-"*20 + " " + "PERIOD " + str(t) + " " + "-"*110
	print "Room" + 36*" " + "Course" + 34*" " + "Enrollment" + " "*(40 - len("Enrollment")) + "Teacher"
	print "-"*140
	for j in range(len(C)):
		# if the course is offered
		if CourseV[j,t] == 1:
			# figure out which room
			for s in R:
				if RoomV[j,s,t] == 1:
					num_enrolled = get_enrollment(j)
					print s + (40 - len(s))*"." + Cd[j] + (40 - len(Cd[j]))*"." \
						+ str(num_enrolled) + "."*(40 - len(str(num_enrolled))) + get_teacher(j)
	print "\n"



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


## OUTPUT FORMATTED FOR SCIP
# for v in m.getVars():
# 	print('%s %g' % (v.varName, v.x))


# if m.getStatus() == "optimal":
#     print("We found an optimal solution!")
# else:
#     print("The problem is", m.getStatus())

# # determine which courses are offered in which period
# offered = {}
# for t in T:
#     class_list = []
#     for j in range(len(C)):
#         if m.getVal(Course[j,t]) == 1:
#             class_list.append(Cd[j])
#     offered[t] = class_list

# # How many courses per period is each student assigned
# for t in T:
#     max_courses = 0
#     min_courses = 1
#     for i in S:
#         num_courses = 0
#         for j in C:
#             if m.getVal(X[i,j]) == 1 and m.getVal(Course[j,t]) ==1:
#                 num_courses += 1
#         if num_courses > max_courses:
#             max_courses = num_courses
#         elif num_courses < min_courses:
#             min_courses = num_courses
#     print("In period", t, "max courses for any student is", max_courses, "and min courses is", min_courses)



# # Print enrollment for each course
# print("Course", (40 -len("Course"))*" ", "Enrolled")
# print("-"*50)
# for j in Cd:
#     num = 0
#     for i in S:
#         if m.getVal(X[i,j]) == 1:
#             num += 1
#     print(Cd[j], (40 - len(Cd[j]))*".", num)




# # Print courses in each period
# for t in T:
#     print("PERIOD", t, "-"*30)
#     for j in Cd:
#         if m.getVal(Course[j,t]) == 1:
#             print(Cd[j])
#     print("\n")




# # Print teachers by period (to ensure no doubles)
# teacher_list = list(I_C_dict.keys())
# for t in T:
#     print("PERIOD", t, "-"*30)
#     for j in Cd:
#         if m.getVal(Course[j,t])==1:
#             for k in range(len(I)):
#                 if Ta[k][j] == 1:
#                     print(I[k])
#     print("\n")







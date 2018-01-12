from pyscipopt import Model, quicksum
import numpy as np
import pandas as pd
import sys, os


def model_setup(STUDENTS, COURSES, schedule1, schedule2, schedule3):
	"""Runs the first part of the modelsetup, creating a model instance,
	creating variables, adding the assignment constraint.
	Returns (in the following order): model instance, variable dictionary"""


	m = Model("Verification")

	# Create Variables
	X = {}
	for i in range(len(STUDENTS)):
	    for j in [1,2,3]:
	        name = STUDENTS[i] + " pref " + str(j)
	        X[i,j] = m.addVar(name, vtype='B')

	# Objective
	m.setObjective(quicksum(3*X[s,1] + 2*X[s,2] + X[s,1] for s in STUDENTS), "maximize")

	# Assignment Constraint (only assigned to one schedule)
	for s in range(len(STUDENTS)):
	    m.addCons(X[s,1] + X[s,2] + X[s,3] == 1)

	return m, X


def read_data():
	"""Reads preferences from the 3 .csv files, returns (in this order):
	dictionary of STUDENTS, COURSES, schedule1, schedule2, schedule3 """

	first = pd.read_csv("TestFirstChoice.csv")
	second = pd.read_csv("TestSecondChoice.csv")
	third = pd.read_csv("TestThirdChoice.csv")

	# Get set of students
	students = first["Student"]
	STUDENTS = {}
	for i in range(len(students)):
	    STUDENTS[i] = students[i]

	# Get set of courses
	courses = first.columns
	COURSES = {}
	for i in range(1,len(courses)):
	    COURSES[i] = courses[i]

	# Extract preferences
	num_students = len(STUDENTS)
	num_courses = len(COURSES)
	schedule1 = np.zeros([num_students, num_courses])
	for i in range(num_students):
	    schedule1[i] = first.iloc[i,1:].tolist()
	    
	schedule2 = np.zeros([num_students, num_courses])
	for i in range(num_students):
	    schedule2[i] = second.iloc[i,1:].tolist()
	    
	schedule3 = np.zeros([num_students, num_courses])
	for i in range(num_students):
	    schedule3[i] = third.iloc[i,1:].tolist()


	return STUDENTS, COURSES, schedule1, schedule2, schedule3


def add_max_cons(MAX, m, X, STUDENTS, COURSES, schedule1, schedule2, schedule3):
	"""Adds the max class size constraint an dreturns the model"""

	for c in range(len(COURSES)):
		m.addCons(quicksum(X[s,1]*schedule1[s,c] + X[s,2]*schedule2[s,c] + X[s,3]*schedule3[s,c]
			for s in range(len(STUDENTS))) <= MAX[c])

	return m


def make_list(given):
	"""makes usable list out of input"""
	x = []
	for i in list(given):
		x.append(int(i))
	return x

def print_results(m, X, STUDENTS, schedule1, schedule2, schedule3):
	"""Takes in a solved model, its variables, and the set of students, and prints 
	the results"""
	
	Results = {}

	if m.getStatus() == "optimal":
		print("\n\n\n\n\n\n\nFound Optimal Solution:\n")
		for i in range(len(STUDENTS)):
			for j in [1,2,3]:
				v = m.getVal(X[i,j])
				if v == 1:
					print(STUDENTS[i], "assigned to choice", str(j))
					Results[STUDENTS[i]] = j
		
		assignment_dict = {1:schedule1, 2:schedule2, 3:schedule3}
		enrollments = [0,0,0,0,0,0]
		for s in Results:
			snum = int(s[-1]) -1# row number in schedule table
			assignment = Results[s] # points to which schedule 
			enrollments = np.add(enrollments, assignment_dict[assignment][snum])
		print("\n")
		for i in range(len(enrollments)):
			print("Course", str(i+1), "has", str(int(enrollments[i])), "students enrolled")

	else:
		print("\n\n\n\n\n\n\nDid not find optimal solution")
		print("Problem is", m.getStatus())


# Disable Print
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore Print
def enablePrint():
    sys.stdout = sys.__stdout__




if __name__=="__main__":
	while True:
		MAX = input("\nInput max class sizes (as series of numbers, e.g. '123'): ")
		if len(MAX) != 6:
			print("Make sure you give 6 numbers")
		else:
			MAX = make_list(MAX)
			STUDENTS, COURSES, schedule1, schedule2, schedule3 = read_data()
			m, X = model_setup(STUDENTS, COURSES, schedule1, schedule2, schedule3)
			m = add_max_cons(MAX, m, X, STUDENTS, COURSES, schedule1, schedule2, schedule3)
			m.optimize()

			
			print_results(m, X, STUDENTS, schedule1, schedule2, schedule3)


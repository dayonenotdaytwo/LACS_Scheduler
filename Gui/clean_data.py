# clean_data.py
# Justina Chen & Kenneth Lipke
# Spring 2018

"""
Contains the data refactoring functions adapted from Justina's 
`CleanDataRefactored.ipynb` notebook
"""

import numpy as np
import csv
import pandas as pd

def create_teacher_info(course_info, out_file_dir):
	"""
	Working from the inital master input of all courses, their subject
	double period, multi-instance, etc., makes a new list of the courses 
	(with multi-instances listed the corresponding number of times)
	this is used to indicate which teachers are teaching which 
	courses

	Parameters
	----------
	course_info - 	a pandas dataframe containing columns `Course Name`, 
					`Number of Instances` (it really should have more, but
					this is all we need for the function to work)

	out_file_name -	the string path to the directory where the output file
					should be saved. Note: the user has no say in what it
					will be called

	Output
	------
	None 	- Saves a new .csv for the user to fill out with teacher names

	add 	- Pandas DataFrame that will be used to build the main input
			  to the LP
	"""
	# create new dataframe to fill
	courses = pd.DataFrame(course_info['Course Name'], 
		columns = ['Course Name', 'Teacher Name'])

	# New dataframe, will eventually copy the input with added rows
	add = pd.DataFrame() 

	# iterate over courses with multiple instances
	for index, row in course_info.loc[course_info['Number of Instances'] >= 1].iterrows():
		instances = np.arange(row['Number of Instances']) + 1
		# add a course for every additional instance
		for i in instances[1:]: 
			c = row['Course Name'] + ' V'+ str(int(i))
			updated_row = row.copy()
			updated_row['Course Name'] = c
			add = add.append(updated_row, ignore_index=True)

	courses = pd.concat([pd.DataFrame(add['Course Name'],
	 columns = ['Course Name']), courses], axis=0).sort_values(by=['Course Name'])
	
	# Save the final file
	file_name = "Teacher_Template.csv"
	full_path = out_file_dir + "/" + file_name
	courses.reset_index(drop=True).to_csv(full_path)

	return add


def create_LP_input(full_course_info, original_course_input):
	"""
	Creates the pandas dataframe that serves as the main input for the LP
	this works off of the dataframe crated by `create_teacher_info`

	Parameters
	----------
	full_course_info - The dataframe produced by create_teacher_info
						(has the multiple instances listed)

	original_course_input - the original file the school is to fill out
							 i.e., the course_info argument to create_teacher_info
	"""
	add = full_course_info # per the way Justina wrote her code

	all_info = pd.concat([original_course_input, add], axis=0).sort_values(by=['Course Name']).reset_index(drop=True)

	# add in double periods 
	add_double = pd.DataFrame() 
	double = all_info.copy()
	double.dropna(subset=['Double Period'])
	for index, row in all_info.loc[all_info['Double Period'] == 'Yes'].iterrows():
		c = row['Course Name'] + ' II'
		updated_row = row.copy()
		updated_row['Course Name'] = c
		updated_row['Double Period'] = 0
		add_double = add_double.append(updated_row, ignore_index=True)    
	all_info = pd.concat([all_info, add_double], axis=0).sort_values(by=['Course Name'])

	# convert "yes" to 1, keep 0
	all_info['Double Period'] = all_info['Double Period'].map({'Yes': 1, 0:0})
	all_info.reset_index(drop=True)

	# add in special ed reqs 
	num_rr = 3
	for room in range(num_rr):
	    rr = pd.Series(['RR'+str(room + 1), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 'Resource'], index=all_info.columns)
	    all_info = all_info.append(rr, ignore_index=True )

	# strip whitespace
	all_info_obj = all_info.select_dtypes(['object'])
	all_info[all_info_obj.columns] = all_info_obj.apply(lambda x: x.str.strip())

	#all_info.to_csv(file_location + '/LP_Input.csv', index=False)
	#print("\n\n\nThis is what would be saved as LP Input:")
	#print(all_info)

	return all_info


# def dept_proximity(file_location, input_file):
def dept_proximity(LP_input):
	"""
	Creates the proximity matrix that indicates if a course belongs to a department. 
	Columns are departments, rows are all courses. 1 if the course is in the dept, 0
	otherwise. The second half of double periods are considered 0. 

	Parameters
	----------
	file_location - The directory where the input_file is located, and where the output file
					Proximity.csv with the proximity matrix will be saved. 

	input_file - the LP input file from which the proximity matrix will be constructed. 
					Needs to be in the file_location directory
	"""
					
	# columns are department, rows are course names
	# info = pd.read_csv(file_location + input_file, delimiter=',')
	info = LP_input

	depts = info[["Course Name", "MS Category", "HS Category"]]
	depts = depts.fillna(0)

	# iterate over depts
	msd = set(depts["MS Category"])
	msd.remove(0)

	hsd = set(depts["HS Category"])
	hsd.remove(0)

	cols = msd.union(hsd)
	single = [subject for subject in cols if '&' not in subject]
	double = [subject for subject in cols if '&' in subject]

	sim = pd.DataFrame(index=depts['Course Name'], columns=single)

	# 2nd period of double courses
	second = np.array(info.loc[info['Double Period'] == 0]['Course Name'])

	for d in cols:  
		dept_courses_MS = depts["Course Name"].loc[depts["MS Category"] == d]
		dept_courses_HS = depts["Course Name"].loc[depts["HS Category"] == d]
		dept_courses = dept_courses_MS.append(dept_courses_HS, ignore_index=True)
		for course in dept_courses:

			# set all 2nd part in double period to 0
			if course in second:
				if '&' in d:
					d1 = d.split(" ")[0]
					d2 = d.split(" ")[2]

					sim.loc[course, d1]=0
					sim.loc[course, d2]=0

				else:
					sim.loc[course, d] = 0

			elif d in single: 
				sim.loc[course, d]=1

			else: #d in double
				# get two depts
				d1 = d.split(" ")[0]
				d2 = d.split(" ")[2]

				sim.loc[course, d1]=1
				sim.loc[course, d2]=1


	sim = sim.fillna(0)            
	# sim.to_csv(file_location + '/Proximity.csv')
	return sim





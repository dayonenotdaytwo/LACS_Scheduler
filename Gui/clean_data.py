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



def create_LP_input(full_course_info, origional_course_input):
	"""
	Creates the pandas dataframe that serces as the main input for the LP
	this works off of the dataframe crated by `create_teacher_info`

	Parameters
	----------
	full_course_info - The dataframe produced by create_teacher_info
						(has the multiple instances listed)

	origional_course_input - the origional file the school is to fill out
							 i.e., the course_info argument to create_teacher_info
	"""
	add = full_course_info # per the way Justina wrote her code

	all_info = pd.concat([origional_course_input, add], axis=0).sort_values(by=['Course Name']).reset_index(drop=True)

	# add in double periods 
	add_double = pd.DataFrame() 
	double = all_info.copy()
	double.dropna(subset=['Double Period'])
	for index, row in all_info.loc[all_info['Double Period'] == 'Yes'].iterrows():
	    c = row['Course Name'] + ' II'
	    updated_row = row.copy()
	    updated_row['Course Name'] = c
	    add_double = add_double.append(updated_row, ignore_index=True)    
	add_double
	all_info = pd.concat([all_info, add_double], axis=0).sort_values(by=['Course Name'])

	# convert "yes" to 1
	all_info['Double Period'] = all_info['Double Period'].map({'Yes': 1})

	return all_info









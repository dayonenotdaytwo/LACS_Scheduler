# Kenneth Lipke
# March 2018
# SavedConfig.py

"""
Class that contains all the relevant information for a saved
configuration of the optimizer, i.e. the course list, the requirements
the preferences

Use:
When you would like to save a configuration, you create an instance of this
class. It also contains a method to pickle, whereby you input the file name,
and the path (likely solicited via a GUI), as well as a method to open 
a configuration

The goal of this class is to save the actual information, as opposed to just
the file names
"""

import pickle
from Requirement import *


class SavedConfig():
	"""
	Fully describe what you will be saving
	"""

	# def __init__(self, initial_file_df, courses, requirements, preference_input,
	# 				LP_input, teacher_file):
	# def __init__(self, initial_file,
	# 					teacher_file,
	# 					preference_file,
	# 					completed_preference_file,
	# 					initial_file_df,
	# 					courses,
	# 					course_list_selected,
	# 					preference_input,
	# 					LP_input,
	# 					requirements):

	def __init__(self,
				initial_file_df,
				courses,
				course_list_selected,
				LP_input,
				teacher_df,
				preference_input_df,
				prox,
				requirements,
				hs_preference_df,
				ms_preference_df,
				rr_df,
				student_dict,
				need_course_num_dict):
		"""
		Saves the required filed

		Parameters
		----------
		courses - List of courses being taught (this does not include the multi
					listings, i.e., just 1 for each, no matter double, etc.)

		requirements - list of Requirement objects 

		prefs - a matrix of student preferences

		LP_input - pandas df that will serve as main input to LP

		teacher_file - mapping teachers to courses

		**These are all the same as we have in the MainApplication fileds**
		"""


		self.initial_file_df = initial_file_df
		self.courses = courses
		self.course_list_selected = course_list_selected
		self.LP_input = LP_input
		self.teacher_df = teacher_df
		self.hs_preference_df = hs_preference_df
		self.ms_preference_df = ms_preference_df
		self.preference_input_df = preference_input_df
		self.prox = prox
		self.rr_df = rr_df
		self.student_dict = student_dict
		self.need_course_num_dict = need_course_num_dict

		self.requirements = None # place holder
		# Check if there are requirements
		if requirements is not None:
			# if so, make MiniRequirements (without Tkinter obejcts)
			# and save them
			for r in requirements:
				self.requirements.append(MiniRequirement(r))




	def save(self, file_path):
		"""
		Saves (pickles) the instance to the given file location
		The location should be queried from an tkinter askfilesave
		"""
		file_path += ".pkl" 
		with open(file_path, 'wb') as output:
			pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
		print("Succesfully Saved")


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

	def __init__(self, initial_file_df, courses, requirements, preference_input,
					LP_input, teacher_file):
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
		self.requirements = requirements
		self.requirements = [] # list of MiniRequirements
		for r in requirements:
			self.requirements.append(MiniRequirement(r))
		self.preference_input = preference_input
		self.LP_input = LP_input
		self.teacher_file = teacher_file



	def save(self, file_path):
		"""
		Saves (pickles) the instance to the given file location
		The location should be queried from an tkinter askfilesave
		"""
		file_path += ".pkl" 
		with open(file_path, 'wb') as output:
			pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
		print("Succesfully Saved")


import numpy as np
import pandas as pd

# import course data from LP_Input.csv
# the index should be the list of courses + the V2 courses.
course_list = pd.DataFrame.from_csv("LP_Input.csv")
course_list = list(course_list.index)

hs_response = pd.DataFrame.from_csv("School form - High School form responses.csv")
ms_response = pd.DataFrame.from_csv("School form - Middle School form responses.csv")
hs_data = hs_response.iloc[:, 2:-2]
ms_data = ms_response.iloc[:, 2:-2]

# extract preference levels from the column names

temp_list = hs_response.columns[2:-2]
temp_list2 = ms_response.columns[2:-2]

# extracted choice numbers from the column names 
hs_choices = []
ms_choices = []

for item in temp_list:
    hs_choices.append(int(item[-2]))
    
for item in temp_list2:
    ms_choices.append(int(item[-2]))
    
# initialize final result of the preprocessing
result = pd.DataFrame(0,columns = course_list, index = range(hs_data.shape[0]+ms_data.shape[0]))

# helper function which returns the corresponding indices in course_list for each row of responses
def course_index(input_array):
    indices = []
    for item in input_array:
        indices.append(course_list.index(item))
    return np.array(indices)

for i in range(hs_data.shape[0]):
    # assign hs_choices values to the corresponding indices in the result data
    result.iloc[i,course_index(hs_data.iloc[i,:])] = hs_choices

    
ms_start_index = hs_data.shape[0]
for i in range(ms_data.shape[0]):
    # assign middle school choices. Row index is num_rows of hs_data + i
    # (so MS rows would be after HS rows in result)
    result.iloc[(ms_start_index + i),course_index(ms_data.iloc[i,:])] = ms_choices
    
result.to_csv("processed_preference_data.csv",index_label=None)
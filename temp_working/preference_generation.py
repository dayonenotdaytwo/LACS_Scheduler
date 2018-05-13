import numpy as np
import pandas as pd

# import course data from LP_Input.csv
# the index should be the list of courses + the V2 courses.
course_list = pd.DataFrame.from_csv("LP_Input.csv")
course_list = list(course_list.index)
course_list.append("place holder") # Deals with N/A (deleted later)


hs_response = pd.DataFrame.from_csv("HSF_5_4.csv")
ms_response = pd.DataFrame.from_csv("MSF_5_4.csv")
hs_data = hs_response.iloc[:, 5:27]
ms_data = ms_response.iloc[:, 5:27]
# change_dict = {'N/A': 'place holder', np.nan:'place holder',
#              "HS English TBA": "Non-Western Writers",
#              'Intermediate Algebra and Geometry': "Discovering Algebra",
#              'Beginning Algebra and Geometry': "Discovering Geometry",
#              'Advanced/In-Depth French': "Advanced French",
#              'Social Studies (BE)': "Governance and Dissent",
#              'MS PE':"MS PE "}
change_dict = {'N/A': 'place holder', np.nan:'place holder',
             "HS English TBA": "Non-Western Writers",
             'Intermediate Algebra and Geometry': "Discovering Algebra",
             'Beginning Algebra and Geometry': "Discovering Geometry",
             'Advanced/In-Depth French': "Advanced French",
             'Social Studies (BE)': "Governance and Dissent"}
for val in change_dict:
    hs_data.replace(val, change_dict[val], inplace=True)
    ms_data.replace(val, change_dict[val], inplace=True)
# hs_data.replace(change_dict, regex=True, inplace=True)
# ms_data.replace(change_dict, regex=True, inplace=True)

# extract preference levels from the column names

temp_list = hs_response.columns[5:27]
temp_list2 = ms_response.columns[5:27]

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
        #print("item is:", item)
        indices.append(course_list.index(item))
    return np.array(indices)

for i in range(hs_data.shape[0]):
    # assign hs_choices values to the corresponding indices in the result data
    #print(i)
    #print("Problem input:", ms_data.iloc[i,:])
    result.iloc[i,course_index(hs_data.iloc[i,:])] = hs_choices

    
ms_start_index = hs_data.shape[0]
for i in range(ms_data.shape[0]):
    #print(i)
    # assign middle school choices. Row index is num_rows of hs_data + i
    # (so MS rows would be after HS rows in result)
    
    result.iloc[(ms_start_index + i),course_index(ms_data.iloc[i,:])] = ms_choices
    
result.drop(["place holder"], axis=1, inplace=True)
result.to_csv("processed_preference_data.csv",index_label=None)


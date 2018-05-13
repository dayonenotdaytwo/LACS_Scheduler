import numpy as np
import pandas as pd

# import course data from LP_Input.csv
# the index should be the list of courses + the V2 courses.
def pref_gen():
    course_list = pd.DataFrame.from_csv("LP_Input.csv")

    course_list = list(course_list.index)
    course_list.append("missing")

    hs_response = pd.DataFrame.from_csv("School form - High School form responses.csv")
    ms_response = pd.DataFrame.from_csv("School form - Middle School form responses.csv")
    hs_response = hs_response.fillna('missing')
    ms_response = ms_response.fillna('missing')
    hs_response = hs_response.drop( 'IIC Mathematics []', axis = 1)

    change_dict = {'N/A': 'place holder', np.nan:'place holder',
                 "HS English TBA": "Non-Western Writers",
                 'Intermediate Algebra and Geometry': "Discovering Algebra",
                 'Beginning Algebra and Geometry': "Discovering Geometry",
                 'Advanced/In-Depth French': "Advanced French",
                 'Social Studies (BE)': "Governance and Dissent",
                 'MS PE':"MS PE "}

    for val in change_dict:
        hs_response.replace(val, change_dict[val], inplace=True)
        ms_response.replace(val, change_dict[val], inplace=True)

    hs_data = hs_response.iloc[:, 5:-10]
    ms_data = ms_response.iloc[:, 5:-10]

    # extract preference levels from the column names

    temp_list = hs_response.columns[5:-10]
    temp_list2 = ms_response.columns[5:-10]

    # extracted choice numbers from the column names 
    hs_choices = []
    ms_choices = []

    for item in temp_list:
        hs_choices.append(int(item[-2]))

    for item in temp_list2:
        ms_choices.append(int(item[-2]))

    # cares only about the first instance of a course in the choice list
    def missing_and_duplicated(x):
        missing = x != 'missing'
        duplicated = x.duplicated()
        missanddup = np.hstack((missing.values.reshape(-1,1), duplicated.values.reshape(-1,1)))
        ind = missanddup.all(axis = 1)
        x[ind] = 'missing'
        return None

    for i in range(hs_data.shape[0]):
        missing_and_duplicated(hs_data.iloc[i,:])
    
    for i in range(ms_data.shape[0]):
        missing_and_duplicated(ms_data.iloc[i,:])

    # helper function which returns the corresponding indices in course_list for each row of responses
    def course_index(input_array):
        indices = []
        for item in input_array:
            indices.append(course_list.index(item))
        return np.array(indices)
    
    result = pd.DataFrame(0,columns = course_list, index = range(hs_data.shape[0]+ms_data.shape[0]))

    for i in range(hs_data.shape[0]):
        # assign hs_choices values to the corresponding indices in the result data
        result.iloc[i,course_index(hs_data.iloc[i,:])] = hs_choices

    ms_start_index = hs_data.shape[0]
    
    for i in range(ms_data.shape[0]):
        # assign middle school choices. Row index is num_rows of hs_data + i
        # (so MS rows would be after HS rows in result)
        result.iloc[(ms_start_index + i),course_index(ms_data.iloc[i,:])] = ms_choices
    
    result['RR1'] = np.zeros(shape=result.shape[0],dtype=np.int32)
    result['RR2'] = np.zeros(shape=result.shape[0],dtype=np.int32)
    result['RR3'] = np.zeros(shape=result.shape[0],dtype=np.int32)
    
    result = result.drop('missing', axis = 1)
    
    return result
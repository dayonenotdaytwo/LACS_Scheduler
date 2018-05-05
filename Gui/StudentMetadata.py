import numpy as np
import pandas as pd


class Student:
    def __init__(self, email="", first_name="", last_name="", s_id="", grade=""):
        """
        Initializes values to empty string if for some reason not given
        """
        if email is not None:
            self.email = email
        else:
            self.email = ""
        if first_name is not None:
            self.first_name = first_name 
        else:
            self.first_name = ""
        if last_name is not None:
            self.last_name = last_name 
        else:
            self.last_name = ""
        if s_id is not None:
            self.s_id = s_id 
        else:
            self.s_id = ""
        if grade is not None:
            self.grade = grade 
        else:
            self.grade = ""

    def __str__(self):
        """
        Overrides pring for this class
        Describes the student
        """
        s = "First Name: " + str(self.first_name)
        s+="\nLast Name:  " + str(self.last_name)
        s+="\nGrade:      " + str(self.grade)
        s+="\nID #:       " + str(self.s_id)
        s+="\nEmail:      n" + str(self.email)

        return s

def metadata(hs_response, ms_response):
    '''
    returns a dictionary of Student objects
    Student keys correspond to str(row) from the processed preferences data

    Parameters
    ----------
    hs_response - pandas dataframe corresponding to the high school
                     response form

    ms_response - pandas datafrome corresponding to the middle school
                        response form
    '''
    # get metadata cols
    hs_data = hs_response.iloc[:, :6]
    ms_data = ms_response.iloc[:, :6]

    # create dictionary to store Students
    students = {}

    for i, row in hs_data.iterrows():
        students[i] = Student(row[1], row[2], row[3], row[4], row[5])

    ms_start_index = hs_data.shape[0]
    for i, row in ms_data.iterrows():
        students[i + ms_start_index] = Student(row[1], row[2], row[3], row[4], row[5])
        
    return students

    #students = metadata("LP_Input.csv", "HSF_5_4.csv", "MSF_5_4.csv")

def get_num_courses(LP_Input, hs_response, ms_response):
    ''' 
    returns a dictionary with num classes by dept for each student 

    Parameters
    ----------
    hs_response - pandas dataframe corresponding to the high school
                     response form

    ms_response - pandas datafrome corresponding to the middle school
                        response form

    LP_Input - the standard LP input dataframe
    '''
    
    # get list of depts
    hs_depts= set(LP_Input["HS Category"])
    ms_depts= set(LP_Input["MS Category"])

    hs_depts = [d for d in hs_depts if str(d) != 'nan']
    ms_depts = [d for d in ms_depts if str(d) != 'nan']

    temp = []
    for d in hs_depts:
        if '&' in d: # cross listed categories
            d1 = d.split('&')[0].strip()
            d2 = d.split('&')[1].strip()
            temp.extend([d1, d2])
        else: temp.append(d)
    hs_depts = sorted(list(set(temp)))


    temp = []
    for d in ms_depts:
        if '&' in d: # cross listed categories
            d1 = d.split('&')[0].strip()
            d2 = d.split('&')[1].strip()
            temp.extend([d1, d2])
        else: temp.append(d)
    ms_depts = sorted(list(set(temp)))

    # get cols where num course responses are
    hs_data = hs_response.iloc[:, 28:36]
    ms_data = ms_response.iloc[:, 31:42]
    
    # generate dictionaries for MS and HS depts
    num_ms = ms_data.shape[0]     # ms offset
    hs_num_courses = {} 
    for d in hs_depts: 
        col = hs_data.filter(like='[' + str(d)).columns
        if(len(col) > 0):
            n = hs_data[col[0]].append(pd.Series(np.zeros(num_ms))).reset_index(drop=True)
            hs_num_courses[d] = n

    num_hs = hs_data.shape[0]    # hs offset    
    ms_num_courses = {}
    for d in ms_depts: 
        col = ms_data.filter(like='[' + str(d)).columns
        if(len(col) > 0):
            n = pd.Series(np.zeros(num_hs)).append(ms_data[col[0]]).reset_index(drop=True)
            ms_num_courses[d] = n
    
    # combine dictionaries
    num_courses_dict = ms_num_courses.copy()
    num_courses_dict.update(hs_num_courses)
    
    return num_courses_dict

    # num_courses("LP_Input.csv", "HSF_5_4.csv", "MSF_5_4.csv")




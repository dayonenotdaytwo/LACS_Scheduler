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
            if type(s_id) == int or type(s_id) == float:
                pass
            elif s_id.isnumeric():
                s_id = int(s_id)
            elif list(s_id.strip()) != []:
                #print("at start", s_id)
                l = list(s_id.strip()) # split it
                l2 = [x for x in l if x.isnumeric()] # keep only numbers
                #print("before problem", l2)
                if l2 != []:
                    # was all words
                    s_id = ''.join(map(str, l2)) # combine to string
                    s_id = int(s_id) # turn back to number
                else:
                    s_id = 0
            else:
                s_id = 0

            self.s_id = s_id 
        else:
            self.s_id = 0
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

def metadata(HSF, MSF):
    '''
    returns a dictionary of Student objects
    Student keys correspond to str(row) from the processed preferences data
    '''

    # load data
    hs_response = pd.read_csv(HSF)
    ms_response = pd.read_csv(MSF)
    
    # get metadata cols
    hs_data = hs_response.iloc[:, :6]
    ms_data = ms_response.iloc[:, :6]

    # create dictionary to store Students
    students = {}

    for i, row in hs_data.iterrows():
        students[str(i)] = Student(row[1], row[2], row[3], row[4], row[5])

    ms_start_index = hs_data.shape[0]
    for i, row in ms_data.iterrows():
        students[str(i + ms_start_index)] = Student(row[1], row[2], row[3], row[4], row[5])
        
    return students

students = metadata("HSF_5_4.csv", "MSF_5_4.csv")

def num_courses(LP_Input, HSF, MSF):
    ''' returns a dictionary with num classes by dept for each student '''
    
    # load data
    hs_response = pd.read_csv(HSF)
    ms_response = pd.read_csv(MSF)
    LP_Input =  pd.read_csv(LP_Input)
    
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

num_courses("LP_Input.csv", "HSF_5_4.csv", "MSF_5_4.csv")

def sim6(num_6th, HSF, MSF, processed_pref_data):
    # 
    '''
    returns a dictionary of Student objects, like metadata() but also
    simulates 6th graders with a first choice pref over all courses that they could take

    Also creates a new file with processed pref data including 6th graders
    called "processed_preference_data_with6.csv"

    '''
    choices =  ['Inquiry and Tools', 'People and Literature', 
                '6th Grade Art', 'Computer Literacy', 'MS Science (Debbie Cowell)',
                'MS Science (Natty Simpson)', 'Roots Music', 'Street Band', 
                'Fiber Tech','MS PE', 'MS/HS PE', 'Spanish A', "Spanish B"]

    pref_data = pd.read_csv(processed_pref_data, index_col = 0)
    start_idx_6th = len(pref_data)
    course_list = pref_data.columns

    ix = np.isin(list(course_list), choices)
    prefs = ix.astype(int)

    sixth_graders = np.tile(prefs, num_6th).reshape((num_6th,len(course_list))) # sim 6th graders as np array
    sixth_graders_df = pd.DataFrame(sixth_graders , columns=course_list) # sim 6th graders as df

    pref_data = pref_data.append(sixth_graders_df, ignore_index = True)
    pref_data.to_csv("processed_preference_data_with6.csv")
    
    # add 6th graders to student dictionary
    students = metadata(HSF, MSF)

    for s in np.arange(start_idx_6th, start_idx_6th + num_6th): 
        # email, first_name, last_name, s_id, grade
        students[str(s)] = Student('DummyEmail'+str(s), 'DummyFName'+str(s), 'DummyLName'+str(s), 'DummyID'+str(s), '6')
    
    return students

sim6_students = sim6(40, "HSF_5_4.csv", "MSF_5_4.csv", "processed_preference_data.csv")
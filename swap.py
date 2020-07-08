from schedule import Schedule
import pandas as pd



OVERLAPS = {'Sa_4': 'Sa_3', 'Sa_5':'Sa_4', 'Su_6':'Su_5', 'Su_7':'Su_6', 'Su_8':'Su_7', 'Su_9':'Su_8'} #dict of slots to check as keys, and overlapping slots as values
SLOTS = ["M_7", "M_9","Tu_7", "Tu_9","W_7", "W_9","Th_7", "Th_9","F_7", "F_9","Sa_3", "Sa_4","Sa_5","Su_5","Su_6","Su_7","Su_8", "Su_9"]
NUM_SLOTS = 16.0 #number of slots
NUM_STUDENTS = 45

def suggest(df, schedule, slot, student):
    """suggests a swap given student in a slot with too little or too much experience"""
    swap_stud = {}
    swap_stud[student] = slot

    #find candidates for swapping
    swap_cands_dict = check_swap(df, schedule, swap_stud)

    return(swap_cands_dict[student])

def max_weight_suggest(schedule, problem, wt, slot, student):
    """suggests a swap given student in a slot with too little or too much experience"""
    student = str(student).replace(" ", "_")
    student = student.replace("-", "_")

    # go through all edges in matching to find edge to be swapped out
    for v in problem.variables():
        if v.varValue > 1e-3:
            #get student-slot variable
            if student in str(v) and slot in str(v):
                old_stud_slot = str(v).split('_')[1:]
                length = len(old_stud_slot)
                # get old slot
                old_slot = old_stud_slot[length - 2] + "_" + old_stud_slot[length - 1]
                #get old student
                old_student = ''
                for i in range(int(length - 3)):
                    old_student += (old_stud_slot[i] + " ")
                old_student = old_student[:-1]
                old_student += ("_" + old_stud_slot[length-3])

    suggested_swaps_unordered = {}
    # go through all other edges in matching to find best edges to be suggested
    for v in problem.variables():
        if v.varValue > 1e-3:
            new_stud_slot = str(v).split('_')[1:] #get student-slot variable
            length = len(new_stud_slot)
            new_slot = new_stud_slot[length - 2] + "_" + new_stud_slot[length - 1] # get new slot
            new_student = '' #get new student
            for i in range(int(length - 3)):
                new_student += (new_stud_slot[i] + " ")
            new_student = new_student[:-1]
            new_student += ("_" + new_stud_slot[length-3])

            #get weights of variable edges and sum them
            w1 = int(wt[old_student][new_slot])
            w2 = int(wt[new_student][old_slot])
            swap_sum = w1 + w2

            #add new_student, new_slot, swap_weight to suggested swap
            suggested_swaps_unordered[str(v)[2:]] = swap_sum

    # reorder dict based on weights (values)
    suggested_swaps = {k: v for k, v in sorted(suggested_swaps_unordered.items(), key=lambda x: x[1], reverse=True)}

    #take students already in slot out of suggested list
    bad_edge_list = []
    for bad_stud in schedule[slot]:
        bad_stud = bad_stud.replace(" ", "_")
        for key in suggested_swaps.keys():
            if str(bad_stud) in str(key):
                bad_edge_list.append(key)

    for bad_edge in bad_edge_list:
        del suggested_swaps[bad_edge]

    return(suggested_swaps)

def check_swap(df, old_sched, unhap_studs):
    """find possible swaps for different TAs to resolve incorrectness """
    swap_dict = {}
    for student in unhap_studs.keys():
        bad_slot = unhap_studs[student]
        swap_dict[student] = []

        # get other students who had unused 3's and 2's on this slot
        swap_candidates = list(df.loc[df[bad_slot] == 3].index)
        swap2_candidates = list(df.loc[df[bad_slot] == 2].index)
        swap_candidates.extend(swap2_candidates)


        # get the student's unused 3's and 2's slots
        unused_slots = []
        unused2_slots = []
        for slot in SLOTS:
            if df.at[student, slot] == 3:
                unused_slots.append(slot)
            if df.at[student, slot] == 2:
                unused2_slots.append(slot)
        unused_slots.extend(unused2_slots)

        # for each swap candidate get their used slots of 3's and 2's
        for cand in swap_candidates:
            swap_slots = []
            swap2_slots = []
            for slot in SLOTS:
                if df.at[cand, slot] == -3:
                    swap_slots.append(slot)
                if df.at[cand, slot] == -2:
                    swap2_slots.append(slot)
            swap_slots.extend(swap2_slots)

            # compare lists of slots if theres a match, add to list of students to swap
            for i_slot in unused_slots:
                for j_slot in swap_slots:
                    if i_slot == j_slot:
                        swap_dict[student].append([cand, i_slot])
    return(swap_dict)

def correct_swap(df, schedule, unhap_studs, swap_dict):
    """use the swap dict from check_swap to do the swap"""
    used = []
    # swap them and update schedule/df
    for student in swap_dict:
        bad_slot = unhap_studs[student]
        #make sure slot hasn't been swapped for yet
        i = 0
        swapped = False
        while(swapped == False):
            new_ta = swap_dict[student][i][0]
            new_slot = swap_dict[student][i][1]
            if [new_ta, new_slot] not in used:
                swap_TA(df, schedule, student, bad_slot, new_ta, new_slot)
                used.append([new_ta, new_slot])
                swapped = True
            else:
                i += 1

def get_unhappy(df):
    unhap_studs = {}
    for student in range(NUM_STUDENTS):
        for slot in SLOTS:
            if df.at[student, slot] == -1:
                unhap_studs[student] = slot
    return(unhap_studs)

def swap_TA(df, sched, old_ta, old_slot, new_ta, new_slot):
    """swap ta's in the schedule at the given slots and update the dataframe"""
    sched.remove_student(old_slot, old_ta)
    sched.remove_student(new_slot, new_ta)
    sched.add_student(old_slot, new_ta)
    sched.add_student(new_slot, old_ta)
    #update df
    update_df(df, old_ta, old_slot)
    update_df(df, old_ta, new_slot)
    update_df(df, new_ta, new_slot)
    update_df(df, new_ta, old_slot)


def update_df(df, student, slot):
    try:
        index = df.loc[df['name'] == student].index[0]
    except:
        print('student not found in df: ', student)
    #update preference table
    score = df.at[index, slot]
    df.at[index, slot] = -(score)
    #update hours worked and happiness
    temp_work = df.at[index, 'hours']
    temp_hap = df.at[index, 'happiness']
    if df.at[index, slot] < 0: #shows they added slot
        df.at[index, 'hours'] = (temp_work + 2)
        df.at[index, 'happiness'] = (temp_hap + score)
    else:
        df.at[index, 'hours'] = (temp_work - 2)
        df.at[index, 'happiness'] = (temp_hap + score)

import re

import numpy as np
import pandas as pd

grade_order = [
    "Exempt", "Modified", "Not Demonstrated", "Unsatisfactory", "Rarely",
    "Below Standard", "Satisfactory", "Sometimes", "Competent", "Good",
    "Very Good", "Usually", "Excellent", "Consistently", "Outstanding"
]

results_dtype = pd.api.types.CategoricalDtype(categories=grade_order,
                                              ordered=True)


def learning_tasks_result_mapper(result):
    if result == "Not Demonstrated":
        return 0.35
    if result == "Below Standard":
        return 0.46
    if result == "Satisfactory":
        return 0.55
    if result == "Competent":
        return 0.64
    if result == "Good":
        return 0.73
    if result == "Very Good":
        return 0.82
    if result == "Excellent":
        return 0.91
    if result == "Outstanding":
        return 1.0
    return float('nan')


def work_habits_result_mapper(result):
    if result == "Unsatisfactory":
        return 0.35
    if result == "Satisfactory":
        return 0.55
    if result == "Good":
        return 0.73
    if result == "Very Good":
        return 0.82
    if result == "Excellent":
        return 1.0
    return np.nan


def progress_report_result_mapper(result):
    if result == "Rarely":
        return 0.25
    if result == "Sometimes":
        return 0.5
    if result == "Usually":
        return 0.75
    if result == "Consistently":
        return 1.0
    return np.nan


progress_report_items = [
    "Completes all set learning", "Contribution in class", "Perseverance",
    "Ready to learn", "Respectfully works/communicates with others",
    "Uses feedback to improve"
]


def gwsc_class_code_parser(class_code, pattern_string):
    m = re.search(pattern_string, class_code)
    if m:
        subject_code = m.group('code')
        # test for Global Goodies vs Geography
        if subject_code == "10GG":
            m = re.search("10GGD[12345]", class_code)
            if m:
                subject_code = "10GL"
        return subject_code
    else:
        print(class_code + " not found")
        return ""

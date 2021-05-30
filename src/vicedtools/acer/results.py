import re
import pandas as pd
import glob
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime

# group report column headings
COL_NAMES_FRONT = ["Unique ID",
                   "Family name",
                   "Given name",
                   "Middle names",
                   "Username",
                   "DOB",
                   "Gender",
                   "Completed",
                   "Year level (current)",
                   "Year level (at time of test)",
                   "Active tags",
                   "Inactive tags",
                   "Tags (at time of test)"]
COL_NAMES_END = ["Score",
                 "Scale",
                 "Stanine",
                 "Percentile"]

RESPONSE_ORDER = ["✓",  "A", "B", "C", "D", "E" ]
RESPONSE_DTYPE = pd.api.types.CategoricalDtype(
                            categories=RESPONSE_ORDER, 
                            ordered=True)


def is_group_report_file(file_location):
    '''Tests whether a given xlsx file contains a PAT Group Report.
    
    Only looks for PAT Reading 5th edition and PAT Maths 4th edition.
    '''
    df = pd.read_excel(file_location, 
                        nrows=1,
                        header=None, 
                        usecols=[0], 
                        names=["Report name"])
    report_name = df["Report name"][0]
    pattern = ("PAT (Reading 5th Edition PAT Reading Test )"
                "|(Maths 4th Edition PAT Maths Test )[0-9]+ - Group Report")
    m = re.search(pattern, report_name)
    if m:
        return True
    else:
        return False

class PATResults:
    '''A class for storing PAT group report data.'''
    def __init__(self, test, number, question_scales, results):
        self.test = test
        self.number = number
        self.question_scales = question_scales
        self.n_questions = len(question_scales)
        self.results = results
        
    @classmethod
    def fromGroupReport(cls,filename):
        temp_df = pd.read_excel(filename, header=None)
        test, number = cls._group_report_metadata(temp_df)
        question_scales = cls._extract_question_scales(temp_df)
        col_names = (COL_NAMES_FRONT 
                     + list(question_scales)  
                     + COL_NAMES_END)
        header_row_id = cls._locate_header_row(temp_df)
        temp_df.drop(temp_df.index[:header_row_id + 1], 
                     inplace=True)
        temp_df.rename(columns={i:col_names[i] for i in range(len(col_names))}, 
                       inplace=True)
        temp_df["Scale"] = temp_df["Scale"].astype(float)
        return cls(test, number, question_scales, temp_df)
    
    @classmethod
    def _group_report_metadata(self,df):
        '''Extract the test (reading/maths) and test number assessed 
        from the group report.
        '''
        report_name = df[0][0]
        pattern = ("PAT (?P<subject>(Reading)|(Maths))"
                   "(( 5th Edition PAT Reading Test )|( 4th Edition PAT Maths Test ))"
                   "(?P<number>[0-9]+) - Group Report")
        m = re.search(pattern, report_name)
        if m:
            return m.group("subject"), m.group("number")
        else:
            raise ValueError("DataFrame did not contain a valid group report.")
    
    @classmethod
    def _extract_question_scales(self, df):
        '''Extract question difficulties from the group report.'''
        question_scales = {}
        if df[0][3] == "Question difficulty":
            current_question = 1
            offset = 12
            while not np.isnan(float(df[current_question + offset][3])):
                question_scales[str(current_question)] = float(df[current_question + offset][3])
                current_question += 1
        # could also extract Strand info from fifth row if present
            return question_scales
        else:
            raise ValueError("DataFrame did not contain expected question scales")

    @classmethod
    def _locate_header_row(self,df):
        '''Returns the row number containing the column header information.'''
        row_id = 0
        while row_id < len(df.index):
            if df[0][row_id] == "Unique ID":
                return row_id
            row_id += 1
        raise ValueError("DataFrame did not contain expected header row.")
            
    def addGroupReport(self,filename):
        temp = PATResults.fromGroupReport(filename)
        if (self.test == temp.test) and (self.number == temp.number):
            self.results = pd.concat([self.results, temp.results],
                                        ignore_index=True)
            self.results.drop_duplicates(subset=["Username", "Completed"],
                inplace=True)
        else:
            raise ValueError("Group report test and number do not match.")
    
    def __add__(self,other):
        if (self.test == other.test) and (self.number == other.number):
            results = pd.concat([self.results, other.results],
                                        ignore_index=True)
            results.drop_duplicates(subset=["Username", "Completed"],
                inplace=True)
            return PATResults(self.test, self.number, self.question_scales, results)

class PATResultsCollection:
    '''A container for PATResults for different tests and test numbers.'''

    def __init__(self):
        self.tests = {"Maths":{},
                      "Reading":{}}
    def addResults(self,patresults):
        '''Adds the given PATResults to the collection.'''
        test = patresults.test
        number = patresults.number
        if number in self.tests[test]:
            self.tests[test][number] += patresults
        else:
            self.tests[test][number] = patresults
    
    def getResults(self,test,number):
        '''Return the results for a particular test and number.'''
        return self.tests[test][number]
    
    def exportScores(self, recent=False):
        '''Exports all PAT scores as a single DataFrame.
        
        Arguments
        recent: if true, only export each student's most recent result
        '''
        export_columns = ['Username',
                            'Completed',
                            'Year level (at time of test)',
                            'Test',
                            'Number',
                            'Score',
                            'Scale',
                            'Score category']
        results_columns = ['Username',
                            'Completed',
                            'Year level (at time of test)',
                            'Score',
                            'Scale']
        export = pd.DataFrame(columns=export_columns)
        
        for test in self.tests:
            for number in self.tests[test]:
                temp = self.tests[test][number].results[results_columns].copy()
                temp['Test'] = test
                temp['Number'] = number
                temp['Score category'] = temp.apply(lambda x: score_categoriser(test, x['Year level (at time of test)'], x["Scale"]), axis=1)
                temp['Completed'] = pd.to_datetime(temp['Completed'], format="%d-%m-%Y %H:%M:%S")
                export = pd.concat([export,temp], ignore_index=True)
        if recent:
            export.sort_values("Completed", ascending=False, inplace=True)
            export.drop_duplicates(subset="Username", inplace=True)
        return export


def score_categoriser(subject, year_level, score):
    '''Returns a qualitative description of a PAT testing result.

    Keyword arguments:
    subject: Reading or Maths, which PAT test the score is for
    year_level: 6 - 10, the year level of the student when they sat the test
    score: the PAT scale score
    '''
    means = {'Reading': {6:128.8, 7: 132.0, 8:134.7, 9: 137.3, 10: 140.4},
            'Maths': {6:127, 7: 130.5, 8: 133.6, 9: 136.5, 10: 139.4}}

    stdevs = {'Reading': {6:12.6, 7: 11.5, 8: 12.2, 9: 12.9, 10: 13.1},
            'Maths': {6:12.0, 7: 12.6, 8: 10.7, 9:11.4, 10: 10.4}}
    # expect year_level as "Year 7"
    year_level_num = int(year_level[5:])
    if year_level_num > 10:
        year_level_num = 10
    z = (score - means[subject][year_level_num])/stdevs[subject][year_level_num]
    if z < - 1.75:
        return "Very low"
    elif z < -0.75:
        return "Low"
    elif z < 0.75:
        return "Average"
    elif z < 1.75:
        return "High"
    else:
        return "Very high"


def group_reports_to_patresults(path, verbose=True):
    '''Reads all PAT group reports in path.

    Keyword arguments
    path: The path in order to search for group report files

    Returns a PATResultsCollection
    '''
    results = PATResultsCollection()
    filenames = glob.glob(path + "*.xlsx")
    filenames = filenames[:6]
    for filename in filenames:
        if is_group_report_file(filename):
            print(filename)
            temp = PATResults.fromGroupReport(filename)
            results.addResults(temp)
    return results


def question_summary(pat_results, question, open_ended=False):
    '''Creates an item results summary for a PAT item.

    '''
    q_difficulty = pat_results.question_scales[question]
    summary_df = pat_results.results[["Scale",question]].copy()
    summary_df["Scale delta"] = summary_df["Scale"] - q_difficulty
    delta_mean = summary_df["Scale delta"].mean()
    if len(summary_df) > 500:
        number_of_categories = 5
        category_width = 10
    elif len(summary_df) > 400:
        number_of_categories = 4
        category_width = 14
    else:
        number_of_categories = 3
        category_width = 18
    categories_offset = round(2 * delta_mean / category_width) # delta_mean divided by half category width
 
    # center category spans over test scale score, if false, test mean is on category boundary
    center_category = categories_offset % 2 != number_of_categories % 2 

    bins = [ q_difficulty 
                - ((number_of_categories - categories_offset) * category_width / 2) 
                + i * category_width 
                for i in range(number_of_categories + 1)]

    center_category_labels = [ "Exceptionally\nbelow", 
                                  "Exceedingly\nbelow", 
                                  "Very\nbelow", 
                                  "Below", 
                                  "Similar", 
                                  "Above", 
                                  "Very\nabove", 
                                  "Exceedingly\nabove", 
                                  "Exceptionally\nabove",
                                  "Extraordinarily\nabove",
                                  "Astronomically\nabove"]
    no_center_category_labels = ["Exceptionally\nbelow", 
                                 "Exceedingly\nbelow", 
                                 "Very\nbelow", 
                                 "Below", 
                                 "Slightly\nbelow", 
                                 "Slightly\nabove", 
                                 "Above", 
                                 "Very\nabove", 
                                 "Exceedingly\nabove", 
                                 "Exceptionally\nabove",
                                 "Extraordinarily\nabove",
                                 "Astronomically\nabove"]
    
    left_limit = 5 + (categories_offset - number_of_categories) //2
    right_limit = (5 + (categories_offset - number_of_categories) //2 
                    + number_of_categories)
    if center_category:
        labels = center_category_labels[left_limit:right_limit]
    else:
        labels = no_center_category_labels[left_limit:right_limit]

    def category_labeller(student_scale,bins,labels,open_ended):
        if not open_ended:
            if student_scale < bins[0] or student_scale > bins[-1]:
                return ""
        for i in range(len(bins)-1):
            if student_scale < bins[i+1]:
                return labels[i]
        return ""
        
    summary_df["Student vs Question"] = summary_df["Scale"].apply(category_labeller, 
                                                            bins=bins, 
                                                            labels=labels, 
                                                            open_ended=open_ended)
    category_dtype = pd.api.types.CategoricalDtype(categories=labels, ordered=True)
    summary_df["Student vs Question"] = summary_df["Student vs Question"].astype(category_dtype)
    summary_df[question] = summary_df[question].astype(RESPONSE_DTYPE)
    summary_df.drop(columns=["Scale delta"], inplace=True)
    
    grouped_df = (summary_df.groupby(["Student vs Question",question]).count() 
                / summary_df.groupby("Student vs Question").count() * 100)\
                .fillna(0).drop(columns=[question])
    counts_df = summary_df.groupby(["Student vs Question",question]).count().rename(columns={"Scale":"Counts"})
    grouped_df["Counts"] = counts_df["Counts"]
    grouped_df = grouped_df.reset_index().rename(columns={question:"Response", "Scale":"Percentage of responses"})
    return grouped_df


def item_analysis_plot(pat_results, question):
    '''Creates an item analysis plot for a single PAT question.
    
    Arguments
    pat_results: an instance of PATResults
    question: which question to create a plot for

    Returns
    f, ax: the matplotlib figure and axes for the plot
    '''
    grouped_df = question_summary(pat_results,question)

    figure_width = len(grouped_df["Student vs Question"].dtype.categories) + 1
    f, ax = plt.subplots(figsize=(figure_width,4))

    sns.lineplot(data=grouped_df, x="Student vs Question", y="Percentage of responses", hue="Response", ax=ax)
    ax.legend(loc="upper left", bbox_to_anchor=(1,1))
    counts = grouped_df.groupby("Student vs Question").sum().reset_index()
    ax.set_xticks(ax.get_xticks())
    x_tick_labels = (counts["Student vs Question"].astype(str) 
                        + "\n(" + counts["Counts"].astype(str) + ")").values
    ax.set_xticklabels(x_tick_labels, fontsize=9)
    ax.legend(loc="upper left", bbox_to_anchor=(1,1))
    ax.set_ylabel("Percentage of responses", fontsize=11)
    ax.set_xlabel("Student ability vs Question difficulty", fontsize=11)
    ax.set_ylim((0,100))
    ax.grid(axis='y',which="both",zorder=0)
    for side, spine in ax.spines.items():
            spine.set_visible(False)
    ax.tick_params(axis='y', colors='white', labelcolor='black')
    ax.set_ylabel("Percentage of responses", fontsize=11)
    ax.set_title(pat_results.test + " Test " + str(pat_results.number) 
                    + ", Question " + question)
    plt.tight_layout()
    return f, ax

def item_analysis_plots(results, save_path="", verbose=True):
    '''Creates item analysis charts for all tests and questions results.
    
    Example usage
    results = group_reports_to_patresults(path_to_group_reports)
    item_analysis_charts(results)

    Arguments
    results: a PATResultsCollection
    save_path="": the directory to save plot images
    verbose=True: whether to print information about charts being created
    '''
    print("Generating PAT item analysis graphs.")
    for test in results.tests:
        for number in results.tests[test]:
            for question in results.tests[test][number].question_scales:
                if verbose:
                    print("Generating graph for " + test 
                            + ", Test " + str(number) 
                            + ", Question " + question)
                filename = (save_path + test + " test " + number 
                            + " question " + question + ".png")
                f, ax = item_analysis_plot(results.tests[test][number],question)
                f.savefig(filename, 
                            dpi=150, 
                            facecolor="white")
                plt.close(f)

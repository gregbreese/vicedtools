import re
import pandas as pd
import glob
import numpy as np

# group report column headings
COL_NAMES_FRONT = [
    "Unique ID", "Family name", "Given name", "Middle names", "Username", "DOB",
    "Gender", "Completed", "Year level (current)",
    "Year level (at time of test)", "Active tags", "Inactive tags",
    "Tags (at time of test)"
]
COL_NAMES_END = ["Score", "Scale", "Stanine", "Percentile"]

RESPONSE_ORDER = ["✓", "A", "B", "C", "D", "E"]
RESPONSE_DTYPE = pd.api.types.CategoricalDtype(categories=RESPONSE_ORDER,
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
    def fromGroupReport(cls, filename):
        temp_df = pd.read_excel(filename, header=None)
        test, number = cls._group_report_metadata(temp_df)
        question_scales = cls._extract_question_scales(temp_df)
        col_names = (COL_NAMES_FRONT + list(question_scales) + COL_NAMES_END)
        header_row_id = cls._locate_header_row(temp_df)
        temp_df.drop(temp_df.index[:header_row_id + 1], inplace=True)
        temp_df.rename(columns={i: col_names[i] for i in range(len(col_names))},
                       inplace=True)
        temp_df["Scale"] = temp_df["Scale"].astype(float)
        temp_df['Completed'] = pd.to_datetime(temp_df['Completed'],
                                              format="%d-%m-%Y %H:%M:%S")
        return cls(test, number, question_scales, temp_df)

    @classmethod
    def _group_report_metadata(self, df):
        '''Extract the test (reading/maths) and test number assessed 
        from the group report.
        '''
        report_name = df[0][0]
        pattern = (
            "PAT (?P<subject>(Reading)|(Maths))"
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
                question_scales[str(current_question)] = float(
                    df[current_question + offset][3])
                current_question += 1
        # could also extract Strand info from fifth row if present
            return question_scales
        else:
            raise ValueError(
                "DataFrame did not contain expected question scales")

    @classmethod
    def _locate_header_row(self, df):
        '''Returns the row number containing the column header information.'''
        row_id = 0
        while row_id < len(df.index):
            if df[0][row_id] == "Unique ID":
                return row_id
            row_id += 1
        raise ValueError("DataFrame did not contain expected header row.")

    def addGroupReport(self, filename):
        temp = PATResults.fromGroupReport(filename)
        if (self.test == temp.test) and (self.number == temp.number):
            self.results = pd.concat([self.results, temp.results],
                                     ignore_index=True)
            self.results.drop_duplicates(subset=["Username", "Completed"],
                                         inplace=True)
        else:
            raise ValueError("Group report test and number do not match.")

    def __add__(self, other):
        if (self.test == other.test) and (self.number == other.number):
            results = pd.concat([self.results, other.results],
                                ignore_index=True)
            results.drop_duplicates(subset=["Username", "Completed"],
                                    inplace=True)
            return PATResults(self.test, self.number, self.question_scales,
                              results)

    def scores(self):
        columns = [
            'Username', 'Gender', 'Completed', 'Year level (at time of test)',
            'Score', 'Scale'
        ]
        temp = self.results[columns].copy()
        temp["Test"] = self.test
        temp["Number"] = self.number
        return temp


class PATResultsCollection:
    '''A container for PATResults for different tests and test numbers.'''

    def __init__(self):
        self.tests = {"Maths": {}, "Reading": {}}

    def addResults(self, patresults):
        '''Adds the given PATResults to the collection.'''
        test = patresults.test
        number = patresults.number
        if number in self.tests[test]:
            self.tests[test][number] += patresults
        else:
            self.tests[test][number] = patresults

    def getResults(self, test, number):
        '''Return the results for a particular test and number.'''
        return self.tests[test][number]

    def exportScores(self, recent=False):
        '''Exports all PAT scores as a single DataFrame.
        
        Arguments
        recent: if true, only export each student's most recent result
        '''
        export_columns = [
            'Username', 'Completed', 'Year level (at time of test)', 'Test',
            'Number', 'Score', 'Scale', 'Score category'
        ]
        results_columns = [
            'Username', 'Completed', 'Year level (at time of test)', 'Score',
            'Scale'
        ]
        export = pd.DataFrame(columns=export_columns)

        for test in self.tests:
            for number in self.tests[test]:
                temp = self.tests[test][number].results[results_columns].copy()
                temp['Test'] = test
                temp['Number'] = number
                temp['Score category'] = temp.apply(lambda x: score_categoriser(
                    test, x['Year level (at time of test)'], x["Scale"]),
                                                    axis=1)
                temp['Completed'] = pd.to_datetime(temp['Completed'],
                                                   format="%d-%m-%Y %H:%M:%S")
                export = pd.concat([export, temp], ignore_index=True)
        if recent:
            export.sort_values("Completed", ascending=False, inplace=True)
            export.drop_duplicates(subset="Username", inplace=True)
        return export

    def scores(self):
        columns = [
            'Username', 'Gender', 'Completed', 'Year level (at time of test)',
            'Score', 'Scale', 'Test', 'Number'
        ]
        scores = pd.DataFrame(columns=columns)
        for test in self.tests:
            for number in self.tests[test]:
                temp = self.tests[test][number].scores()
                scores = pd.concat([scores, temp], ignore_index=True)
        return scores


def score_categoriser(subject, year_level, date, score):
    '''Returns a qualitative description of a PAT testing result.

    Keyword arguments:
    subject: "Reading" or "Maths", which PAT test the score is for
    year_level: "Year 5", "Year 6", "Year 7", ..., "Year 10"
        the year level of the student when they sat the test
    score: the PAT scale score
    '''
    means = {
        'Reading': {
            6: 128.8,
            7: 132.0,
            8: 134.7,
            9: 137.3,
            10: 140.4
        },
        'Maths': {
            6: 127,
            7: 130.5,
            8: 133.6,
            9: 136.5,
            10: 139.4
        }
    }

    stdevs = {
        'Reading': {
            6: 12.6,
            7: 11.5,
            8: 12.2,
            9: 12.9,
            10: 13.1
        },
        'Maths': {
            6: 12.0,
            7: 12.6,
            8: 10.7,
            9: 11.4,
            10: 10.4
        }
    }
    # expect year_level as "Year 7"
    year_level_num = int(year_level[5:])
    if date.month <= 4:
        year_level_num -= 1
    if year_level_num > 10:
        year_level_num = 10
    z = (score -
         means[subject][year_level_num]) / stdevs[subject][year_level_num]
    if z < -1.75:
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
    for filename in filenames:
        if is_group_report_file(filename):
            print(filename)
            temp = PATResults.fromGroupReport(filename)
            results.addResults(temp)
    return results

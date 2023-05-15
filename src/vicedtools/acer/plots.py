# Copyright 2021 VicEdTools authors

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Functions for creating visualisations of PAT results."""

from __future__ import annotations

import json
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from vicedtools.acer.patresults import RESPONSE_DTYPE, PATResults, PATResultsCollection


def question_summary(pat_results: PATResults,
                     question: str,
                     open_ended=False,
                     from_date=None,
                     to_date=None) -> pd.DataFrame:
    '''Creates an item analysis summary for a PAT item.

    Groups the students by their scale score and then for each group determines
    the proportion of students that selected each response option. Groups the
    students in three to five bins depending on how many students there are.
    Centers the bins based on the distribution of student scale scores and
    labels the bins based on their relative level compared to the question.

    Students with higher scale scores should be observed to select the correct
    response more often.

    Used by item_analysis_plot to summarise item results.

    Args:
        pat_results: An instance of PATResults to summarise.
        question: Which question number to produce a summary of.
        open_ended: Optional; If true, then include outliers in the outermost 
            bins. Otherwise, these students are exluded from the plot.

    Returns:
        A pandas DataFrame with these columns.
            'Student v Question': A qualitative description of the relative
                scale score of the students compared to the item. 
            'Response': 'A', 'B', 'C', 'D', 'E', or '✓'.
            'Percentage of responses': as float
    '''
    q_difficulty = pat_results.question_scales[question]
    if from_date and to_date:
        rows = (pat_results.results["Completed"] >
                from_date) & (pat_results.results["Completed"] < to_date)
        summary_df = pat_results.results.loc[rows, ["Scale", question]].copy()
    elif from_date:
        rows = (pat_results.results["Completed"] > from_date)
        summary_df = pat_results.results.loc[rows, ["Scale", question]].copy()
    elif to_date:
        rows = (pat_results.results["Completed"] < to_date)
        summary_df = pat_results.results.loc[rows, ["Scale", question]].copy()
    else:
        summary_df = pat_results.results[["Scale", question]].copy()
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
    categories_offset = round(
        2 * delta_mean /
        category_width)  # delta_mean divided by half category width

    # center category spans over test scale score, if false, test mean is on category boundary
    center_category = categories_offset % 2 != number_of_categories % 2

    bins = [
        q_difficulty -
        ((number_of_categories - categories_offset) * category_width / 2) +
        i * category_width for i in range(number_of_categories + 1)
    ]

    center_category_labels = [
        "Exceptionally\nbelow", "Exceedingly\nbelow", "Very\nbelow", "Below",
        "Similar", "Above", "Very\nabove", "Exceedingly\nabove",
        "Exceptionally\nabove", "Extraordinarily\nabove",
        "Astronomically\nabove"
    ]
    no_center_category_labels = [
        "Exceptionally\nbelow", "Exceedingly\nbelow", "Very\nbelow", "Below",
        "Slightly\nbelow", "Slightly\nabove", "Above", "Very\nabove",
        "Exceedingly\nabove", "Exceptionally\nabove", "Extraordinarily\nabove",
        "Astronomically\nabove"
    ]

    left_limit = 5 + (categories_offset - number_of_categories) // 2
    right_limit = (5 + (categories_offset - number_of_categories) // 2 +
                   number_of_categories)
    if center_category:
        labels = center_category_labels[left_limit:right_limit]
    else:
        labels = no_center_category_labels[left_limit:right_limit]

    def category_labeller(student_scale, bins, labels, open_ended):
        if not open_ended:
            if student_scale < bins[0] or student_scale > bins[-1]:
                return ""
        for i in range(len(bins) - 1):
            if student_scale < bins[i + 1]:
                return labels[i]
        return ""

    summary_df["Student vs Question"] = summary_df["Scale"].apply(
        category_labeller, bins=bins, labels=labels, open_ended=open_ended)
    category_dtype = pd.api.types.CategoricalDtype(categories=labels,
                                                   ordered=True)
    summary_df["Student vs Question"] = summary_df[
        "Student vs Question"].astype(category_dtype)
    summary_df[question] = summary_df[question].astype(RESPONSE_DTYPE)
    summary_df.drop(columns=["Scale delta"], inplace=True)

    grouped_df = (summary_df.groupby(["Student vs Question",question]).count()
                / summary_df.groupby("Student vs Question").count() * 100)\
                .fillna(0).drop(columns=[question])
    counts_df = summary_df.groupby(
        ["Student vs Question",
         question]).count().rename(columns={"Scale": "Counts"})
    grouped_df["Counts"] = counts_df["Counts"]
    grouped_df = grouped_df.reset_index().rename(columns={
        question: "Response",
        "Scale": "Percentage of responses"
    })
    return grouped_df


def item_analysis_plot(pat_results: PATResults,
                       question: str,
                       from_date=None,
                       to_date=None) -> tuple[plt.Figure, plt.Axes]:
    '''Creates an item analysis plot for a single PAT question.
    
    Compares the expected performance of students on an item, based on their
    PAT scale score and the question's scale score, with their responses.
    The correct response is expected to be selected more often by students with
    higher scale scores.

    Args:
        pat_results: An instance of PATResults to analyse.
        question: The question number to produce a plot for.

    Returns:
        f, ax: the matplotlib figure and axes for the plot
    '''
    grouped_df = question_summary(pat_results,
                                  question,
                                  from_date=from_date,
                                  to_date=to_date)

    figure_width = len(grouped_df["Student vs Question"].dtype.categories) + 1
    f, ax = plt.subplots(figsize=(figure_width, 4))

    sns.lineplot(data=grouped_df,
                 x="Student vs Question",
                 y="Percentage of responses",
                 hue="Response",
                 ax=ax)
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    counts = grouped_df.groupby("Student vs Question").sum().reset_index()
    ax.set_xticks(ax.get_xticks())
    x_tick_labels = (counts["Student vs Question"].astype(str) + "\n(" +
                     counts["Counts"].astype(str) + ")").values
    ax.set_xticklabels(x_tick_labels, fontsize=9)
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    ax.set_ylabel("Percentage of responses", fontsize=11)
    ax.set_xlabel("Student ability vs Question difficulty", fontsize=11)
    ax.set_ylim((0, 100))
    ax.grid(axis='y', which="both", zorder=0)
    for side, spine in ax.spines.items():
        spine.set_visible(False)
    ax.tick_params(axis='y', colors='white', labelcolor='black')
    ax.set_ylabel("Percentage of responses", fontsize=11)
    ax.set_title(pat_results.test + " Test " + str(pat_results.number) +
                 ", Question " + question)
    plt.tight_layout()
    return f, ax


def item_analysis_plots(results: PATResultsCollection,
                        save_path: str = "",
                        verbose: bool = True,
                        from_date=None,
                        to_date=None) -> None:
    '''Creates item analysis charts for all tests and questions results.
    
    Creates a chart for each question in each PAT test found in the provided
    PATResultsCollection and saves each chart as a .png.
    Files are saved using the format "[save_path][Reading/Maths] test [test number] question [question number].png"

    Example usage:
        results = group_reports_to_patresults(path_to_group_reports)
        item_analysis_charts(results)

    Args:
        results: a PATResultsCollection instance to produce plots from
        save_path="": Optional; the path to save plot images to
        verbose=True: Optional; if True, print information about each chart as
            it is generated.
    '''
    print("Generating PAT item analysis graphs.")
    for test in results.tests:
        for number in results.tests[test]:
            for question in results.tests[test][number].question_scales:
                if from_date and to_date:
                    rows = sum((results.tests[test][number].results["Completed"]
                                < to_date) &
                               (results.tests[test][number].results["Completed"]
                                > from_date))
                elif from_date:
                    rows = sum(results.tests[test][number].results["Completed"]
                               > from_date)
                elif to_date:
                    rows = sum(results.tests[test][number].results["Completed"]
                               < to_date)
                else:
                    rows = len(results.tests[test][number].results)
                if rows > 3:
                    if verbose:
                        print("Generating graph for " + test + ", Test " +
                              str(number) + ", Question " + question)
                    filename = (save_path + test + " test " + number +
                                " question " + question + ".png")
                    f, ax = item_analysis_plot(results.tests[test][number],
                                               question,
                                               from_date=from_date,
                                               to_date=to_date)
                    f.savefig(filename, dpi=150, facecolor="white")
                    plt.close(f)


def time_series_background_coords(scale_constructs_json,
                                  cmap=mpl.colormaps['PiYG']):
    with open(scale_constructs_json, 'r') as f:
        scale_constructs = json.load(f)

    xs = [0.84, 1.84, 2.84, 3.84, 4.84, 5.84, 6.84, 7.84, 8.84, 9.84, 10]
    background_coords = {}
    background_coords['xs'] = xs

    tests = ["Reading", "Maths"]
    for test in tests:
        # find scale construct for test
        for key in scale_constructs:
            if test in scale_constructs[key]['name']:
                scale_construct = scale_constructs[key]

        # extract percentiles for the test from the Australian norm sample
        percentiles = ['5', '25', '75', '95']
        norm_values = {}
        for percentile in percentiles:
            norm_values[percentile] = []
            for yr in scale_construct['metadata']['normReferencedLevels']:
                norm_values[percentile].append(
                    yr['percentiles'][percentile]['scaleScore'])
        # add extrapolated percentile values for the end of Year 10 (treating the Year 10 result as for October/November)
        for percentile in ['5', '25', '75', '95']:
            norm_values[percentile].append(norm_values[percentile][-1] +
                                           (norm_values[percentile][-1] -
                                            norm_values[percentile][-2]) * 0.16)

        background_coords[test] = {
            'Well above expected level': {},
            'Above expected level': {},
            'At expected level': {},
            'Below expected level': {},
            'Well below expected level': {},
        }
        background_coords[test]['Well above expected level']['top'] = [
            200 for _ in range(len(xs))
        ]
        background_coords[test]['Well above expected level'][
            'bottom'] = norm_values['95']
        background_coords[test]['Above expected level']['top'] = norm_values[
            '95']
        background_coords[test]['Above expected level']['bottom'] = norm_values[
            '75']
        background_coords[test]['At expected level']['top'] = norm_values['75']
        background_coords[test]['At expected level']['bottom'] = norm_values[
            '25']
        background_coords[test]['Below expected level']['top'] = norm_values[
            '25']
        background_coords[test]['Below expected level']['bottom'] = norm_values[
            '5']
        background_coords[test]['Well below expected level'][
            'top'] = norm_values['5']
        background_coords[test]['Well below expected level']['bottom'] = [
            0 for _ in range(len(xs))
        ]

        background_coords[test]['Well above expected level']['colour'] = cmap(
            200)
        background_coords[test]['Above expected level']['colour'] = cmap(164)
        background_coords[test]['At expected level']['colour'] = cmap(128)
        background_coords[test]['Below expected level']['colour'] = cmap(92)
        background_coords[test]['Well below expected level']['colour'] = cmap(
            56)

    return background_coords


def student_time_series_plot(scores, background_coords):
    plt.rcParams.update({
        'font.sans-serif': 'Arial',
        'font.family': 'sans-serif'
    })

    # Create the figure and axes
    fig = plt.figure(figsize=(9.5, 4))
    gs = fig.add_gridspec(3,
                          3,
                          width_ratios=(9, 9, 1),
                          height_ratios=[1, 2, 1],
                          left=0.1,
                          right=0.9,
                          bottom=0.1,
                          top=0.9,
                          wspace=0.35,
                          hspace=0.05)
    axs = {}
    axs["Reading"] = fig.add_subplot(gs[:, 0])
    axs["Maths"] = fig.add_subplot(gs[:, 1])
    cbar = fig.add_subplot(gs[1, 2])

    tests = ["Reading", "Maths"]
    for test in tests:
        ax = axs[test]

        selected = scores.loc[scores["Test"] == test]

        # If there are no results for the student,  output axes with a No Results mesage
        if len(selected) == 0:
            for side, spine in ax.spines.items():
                spine.set_color('dimgrey')
                spine.set_visible(False)
            ax.set_title(f"PAT {test}", fontsize=16)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.text(0.5, 0.5, "No Results", ha="center")
            continue

        # plot the scores
        ax.errorbar(selected["Year level number"],
                    selected["Scale"],
                    yerr=selected["Error"],
                    linewidth=0,
                    elinewidth=1,
                    color="dimgrey")
        ax.plot(selected["Year level number"],
                selected["Scale"],
                marker=".",
                ms=12,
                linewidth=0,
                color="dimgrey",
                zorder=3)
        # shade the background to indicate average/above/below/etc scores
        for category, data in background_coords[test].items():
            ax.fill_between(background_coords['xs'],
                            data['bottom'],
                            data['top'],
                            color=data['colour'],
                            zorder=1)

        # format the graph
        ax.set_xlim((6, 10))
        y_min = min(
            selected["Scale"].min(),
            background_coords[test]['Well below expected level']['top'][6]) - 5
        y_max = max(
            selected["Scale"].max(), background_coords[test]
            ['Well above expected level']['bottom'][6]) + 5
        ax.set_ylim((y_min, y_max))
        ax.tick_params(axis="x", which='both', length=0)
        ax.set_xticks([i for i in range(6, 11)])
        ax.set_xticklabels([])
        ax.set_xticks([i + 0.5 for i in range(6, 10)], minor=True)
        ax.set_xticklabels([str(i) for i in range(7, 11)], minor=True)
        ax.set_ylabel("PAT Score", fontsize=12)
        ax.set_xlabel("Year level", fontsize=12)
        ax.grid(axis="x", zorder=0)
        for side, spine in ax.spines.items():
            spine.set_color('dimgrey')
            spine.set_visible(True)
        ax.set_title(f"PAT {test}", fontsize=16)

    # match y axes limits for both graphs
    y_min = min(axs['Reading'].get_ylim()[0], axs['Maths'].get_ylim()[0])
    y_max = min(axs['Reading'].get_ylim()[1], axs['Maths'].get_ylim()[1])
    axs['Reading'].set_ylim((y_min, y_max))
    axs['Maths'].set_ylim((y_min, y_max))

    # create key
    cbar.fill_between([0, 1], [0, 0], [5, 5],
                      color=background_coords['Reading']
                      ['Well below expected level']['colour'])
    cbar.fill_between(
        [0, 1], [5, 5], [25, 25],
        color=background_coords['Reading']['Below expected level']['colour'])
    cbar.fill_between(
        [0, 1], [25, 25], [75, 75],
        color=background_coords['Reading']['At expected level']['colour'])
    cbar.fill_between(
        [0, 1], [75, 75], [95, 95],
        color=background_coords['Reading']['Above expected level']['colour'])
    cbar.fill_between([0, 1], [95, 95], [100, 100],
                      color=background_coords['Reading']
                      ['Well above expected level']['colour'])
    cbar.set_xticks([])
    cbar.set_yticks([])
    cbar.set_ylim((0, 100))
    cbar.set_title("Key", pad=15, fontsize=12)
    cbar.text(1.1, 50, "At expected level", va="center")
    cbar.text(1.1, 15, "Below expected level", va="center")
    cbar.text(1.1, 2.5, "Well below expected level", va="center")
    cbar.text(1.1, 85, "Above expected level", va="center")
    cbar.text(1.1, 97.5, "Well above expected level", va="center")
    for side, spine in cbar.spines.items():
        spine.set_visible(False)

    return fig


def student_time_series_plots(
    pat_scores_csv: str,
    student_details_csv: str,
    scale_constructs_json: str,
    save_dir=".",
    cmap: mpl.colors.Colormap = mpl.colormaps['PiYG'],
):
    """Creates a time series plot of the pat results of all students.
    
    Args:
        pat_scores_csv: The path to a csv containing a pat score summary, as
            exported from PAT_Sittings.
        student_details_csv: The path to a csv containing student details, as
            exported from CompassSession.
        scale_constructs_json: The path to a saved scale_constructs_json, as
            exported from OARS.
        save_dir: The path to save the images of each plot. Will save using a
            directory structure of save_dir/<year level>/<form group>/ with each
            image saved as "<student code> <student name> pat timeseries.png"
        cmap: A diverging colormap to use for indicating results are above or
            below average.
    """
    background_coords = time_series_background_coords(scale_constructs_json,
                                                      cmap=cmap)

    scores = pd.read_csv(pat_scores_csv)
    scores.rename(columns={"SUSSI ID": "StudentCode"}, inplace=True)
    scores["Completed"] = pd.to_datetime(scores["Completed"])
    scores["Year level number"] = (
        scores["Year level (at time of test)"].astype(float) - 1 +
        scores["Completed"].apply(lambda x: x.timetuple().tm_yday) / 365)

    students = pd.read_csv(student_details_csv)
    students = students.loc[students["Status"] == "Active"].copy()
    students.rename(columns={"SUSSI ID": "StudentCode"}, inplace=True)
    students["Full Name"] = students["Preferred Name"] + " " + students[
        "Last Name"].str.title()
    students.set_index("StudentCode", inplace=True)

    student_codes = pd.concat([scores["StudentCode"], students.index]).unique()
    for student_code in student_codes:
        selected_scores = scores.loc[scores["StudentCode"] == student_code]

        fig = student_time_series_plot(selected_scores, student_code,
                                       background_coords)

        student = students.loc[student_code]
        if len(selected_scores) > 0:
            path = os.path.join(
                save_dir, f"{student['Year Level']}/{student['Form Group']}")
            if not os.path.exists(path):
                os.makedirs(path)
            fig.savefig(
                f"{path}/{student_code} {student['Full Name']} PAT timeseries.png",
                facecolor='w',
                dpi=150,
                bbox_inches='tight')
            plt.close(fig)

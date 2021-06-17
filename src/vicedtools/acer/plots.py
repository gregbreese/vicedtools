import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from vicedtools.acer.patresults import RESPONSE_DTYPE

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

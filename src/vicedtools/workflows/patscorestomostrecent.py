import os

import pandas as pd

def pat_scores_to_most_recent(oars_dir: str):
    summary_df = pd.read_csv(os.path.join(oars_dir, "pat scores.csv"))
    # get only most recent result for each test
    summary_df.sort_values("Completed", ascending=False, inplace=True)
    summary_df.drop_duplicates(subset=["Username", "Test"], inplace=True)

    recent_wide = summary_df.pivot(index="Username", columns="Test")
    recent_wide.columns = [f"{b} {a}" for (a,b) in recent_wide.columns]
    recent_wide.reset_index(inplace=True)

    recent_wide.to_csv(os.path.join(oars_dir, "pat most recent.csv"), index=False)

if __name__ == "__main__":
    from config import (root_dir,
                        oars_folder)

    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    oars_dir = os.path.join(root_dir, oars_folder)
    if not os.path.exists(oars_dir):
        raise FileNotFoundError(f"{oars_dir} does not exist as a directory.")

    pat_scores_to_most_recent(oars_dir)
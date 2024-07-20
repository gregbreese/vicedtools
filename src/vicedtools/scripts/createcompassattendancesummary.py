# Copyright 2024 VicEdTools authors

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Executable script for creating a Compass attendance summary csv."""

import glob

import numpy as np
import pandas as pd

from vicedtools.scripts.config import (attendance_halfday_dir,
                                        compass_dir,)

present_codes = [100,600,602,603,604,606,608,609,611,612,613,614,620,624,111,112,113,114,116,117,118,119]
absent_codes = [200,203,204,205,208,210,211,212,300,400,401,500,804,805,806,807]
na_codes = [626,901,902,903,904,919,929,701,702,801,804]

files = glob.glob(f"{attendance_halfday_dir}/CASES21_HalfDay *.csv")
columns = ["StudentCode", "Date", "Year Level", "AM", "PM"]
temp_dfs = []
for file in files:
    temp_df = pd.read_csv(file, names=columns,skiprows=1)
    temp_dfs.append(temp_df)
attendance = pd.concat(temp_dfs)

attendance = attendance.melt(id_vars=["StudentCode","Date","Year Level"], value_vars=['AM','PM'], var_name="AM/PM", value_name="Code")

present_rows = attendance["Code"].isin(present_codes)
absent_rows = attendance["Code"].isin(absent_codes)
na_rows = attendance["Code"].isin(na_codes)
attendance.loc[present_rows,"Value"] = 1
attendance.loc[absent_rows,"Value"] = 0
attendance.loc[na_rows,"Value"] = np.nan

(attendance
 .loc[:,['StudentCode',"Date","Value"]]
 .groupby(['Date','StudentCode',])
 .mean()
 .reset_index()
 .dropna(subset="Value")
 .to_csv(f"{compass_dir}/attendance summary.csv", index=False)
)
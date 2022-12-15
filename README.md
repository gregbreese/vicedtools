# vicedtools

This is a collection of utility tools for working with school data in Victorian schools.

The utilities have been designed to be state-less. Where tools have been created to export data then they have been designed to work with the native export formats provided by the relevant sites so that processing functions also integrate with existing data stores.

Currently includes tools for:

- automating the exporting of data from Compass, ACER's OARS site, the VCAA data service (NAPLAN) and VASS (VCE results).
- tools for working with ACER's OARS site, such as working with PAT data
- extracting NAPLAN data from the SSSR data.js file
- uploading data to Google Cloud storage and BigQuery for use with Data Studio

The core export functions are provided by the CompassSession, OARSSession, VASSSession and DataServiceSession classes.

See workflows/sample_config.py for a sample config file.

All previous WebDriver-based exporting modules have now had requests.Session based versions implemented!

## Getting started

### Installation

Install from [`pip`](https://pypi.org/project/vicedtools/)

```shell
pip3 install vicedtools
```

### 

Create a `config.py` file if using the workflow scripts. Use the [`config_sample.py`](/src/vicedtools/workflows/config_sample.py) as a starting point.

## Usage

### Exporting from VASS
Create a session and select a year.
```python
from vicedtools import VASSSession
grid_password = [('1', '1'), ('8', '1'), ('4', '5'), ('5', '5'), ('1', '8'), 
                 ('8', '8')]
s = VASSSession(username=username,
            password=password,
            grid_password=grid_password)
year = "2021"
s.change_year("year")
```
Exports from the main VASS interface.
```python
s.personal_details_summary(f"personal details summary {year}.csv")
s.school_program_summary(f"school program summary {year}.csv")
s.gat_summary(f"gat scores {year}.csv")
s.school_scores(f"school scores {year}.csv")
s.external_results(f"external scores {year}.csv")
s.moderated_coursework_scores(f"moderated coursework scores {year}.csv")
```
Some data is only available once the VCE data service is updated.
```python
s.predicted_scores(f"predicted scores {year}.csv")
```

### Exporting from OARS
Create a session.
```python
from vicedtools import OARSSession, OARSBasicAuthenaticator
oars_authenticator = OARSBasicAuthenaticator(oars_username, oars_password)
s = OARSSession(oars_school_code, oars_authenticator)
```
Exporting student details.
```python
candidates = s.get_candidates()
with open("oars_candidates.json", 'w') as f:
    json.dump(candidates, f)
```
Export staff details.
```python
s.get_staff_xlsx("oars_staff.xlsx")
```
Export test results.
```python
sittings = s.get_all_pat_sittings("01=01-2020", "31-12-2021")
with open("sittings 01-01-2020 31-12-2021.json", 'w') as f:
    json.dump(sittings, f)
```

### Exporting NAPLAN results from the VCAA data service
Create a session.
```python
from vicedtools.naplan import DataserviceSession, DataServiceBasicAuthenticator
dataservice_authenticator = DataServiceBasicAuthenticator(
    dataservice_username, dataservice_password)
s = DataserviceSession(dataservice_authenticator)
```
Export outcome Excel files.
```python
s.export_naplan("2021, "./naplan results/")
```
Export the SSSR.
```python
s.export_sssr("2021, "./naplan sssr/")
```
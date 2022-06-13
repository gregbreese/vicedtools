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

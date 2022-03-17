import os

import pandas as pd

from vicedtools.compass import CompassWebDriver, CompassAuthenticator

def export_compass_sds(gecko_path: str, school_code: str, authenticator: CompassAuthenticator,  export_dir: str):
    """Exports student details from Compass.

    Args:
        gecko_path: The path to geckodiver.exe
        school_code: The compass school string. E.g. https://{school_code}.compass.education
        authenticator: An instance of CompassAuthenticator.
        export_dir: The folder to save the SDS export data to.
    """
    driver = CompassWebDriver(compass_school_code, gecko_path, compass_authenticator)
    driver.export_sds(export_dir)
    driver.quit()


if __name__ == "__main__":
    from config import (root_dir, 
                        compass_folder, 
                        sds_folder,
                        gecko_path, 
                        compass_authenticator,
                        compass_school_code)

    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir} is not a directory.")
    compass_dir = os.path.join(root_dir, compass_folder)
    if not os.path.exists(compass_dir):
        os.mkdir(compass_dir)
    sds_dir = os.path.join(compass_dir, sds_folder)
    if not os.path.exists(sds_dir):
        os.mkdir(sds_dir)

    export_compass_sds(gecko_path, compass_school_code, compass_authenticator, sds_dir)


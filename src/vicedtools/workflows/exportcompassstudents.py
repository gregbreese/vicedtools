import os

import pandas as pd

from vicedtools.compass import CompassWebDriver, CompassAuthenticator

def export_compass_students(gecko_path: str, school_code: str, authenticator: CompassAuthenticator,  file_name: str):
    """Exports student details from Compass.

    Args:
        gecko_path: The path to geckodiver.exe
        school_code: The compass school string. E.g. https://{school_code}.compass.education
        authenticator: An instance of CompassAuthenticator.
        file_name: The filename to save the student csv data to.
    """
    driver = CompassWebDriver(compass_school_code, gecko_path, compass_authenticator)
    driver.export_student_details(file_name, detailed=True)
    driver.quit()


if __name__ == "__main__":
    from config import (root_dir, 
                        compass_folder, 
                        student_details_folder,
                        student_details_csv,
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
    student_details_dir = os.path.join(compass_dir, student_details_folder)
    if not os.path.exists(student_details_dir):
        os.mkdir(student_details_dir)
    student_details_file = os.path.join(student_details_dir, student_details_csv)

    export_compass_students(gecko_path, compass_school_code, compass_authenticator, student_details_file)

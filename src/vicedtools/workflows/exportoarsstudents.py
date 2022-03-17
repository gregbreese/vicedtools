import json
import os

from vicedtools.acer.oars import OARSSession

def export_oars_students(school_code, authenticator, export_dir):
    """Exports OARS student data and saves it in candidates.json.

    Args:
        school_code: An OARS school string. E.g. https://oars.acer.edu.au/{your school string}/...
        authenticator: An instance of OARSAuthenticator.
        export_dir: The directory to save the candidate data in.
    """
    export_file = os.path.join(export_dir, "candidates.json")

    s = OARSSession(school_code, authenticator)
    candidates = s.get_candidates()
    with open(export_file, 'w') as f:
        json.dump(candidates, f)

if __name__ == "__main__":
    from config import (root_dir,
                        oars_folder,
                        oars_authenticator,
                        oars_school_code)

    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir} is not a directory.")
    oars_dir = os.path.join(root_dir, oars_folder)
    if not os.path.exists(oars_dir):
        os.mkdir(oars_dir)

    export_oars_students(oars_school_code, oars_authenticator, oars_dir)
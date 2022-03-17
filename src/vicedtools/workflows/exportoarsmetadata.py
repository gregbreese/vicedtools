import json
import os

from vicedtools.acer.oars import OARSSession

def export_oars_metadata(school_code, authenticator, export_dir):
    """Exports PAT test metadata.
    
    Saves test metadata in tests.json.
    Saves scale construct metadata in scaleconstructs.json

    Args:
        school_code: An OARS school string. E.g. https://oars.acer.edu.au/{your school string}/...
        authenticator: An instance of OARSAuthenticator.
        export_dir: The directory to save the test data in.
    """
    tests_file = os.path.join(oars_path, "tests.json")
    s = OARSSession(oars_school_code, oars_authenticator)
    with open(tests_file, 'w') as f:
        json.dump(s.tests, f)

    scale_constructs_file = os.path.join(oars_path, "scaleconstructs.json")
    s = OARSSession(oars_school_code, oars_authenticator)
    with open(scale_constructs_file, 'w') as f:
        json.dump(s.scale_constructs, f)

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
    
    export_oars_metadata(oars_school_code, oars_authenticator, oars_dir)
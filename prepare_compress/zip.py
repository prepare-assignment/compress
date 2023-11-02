import os
from pathlib import Path
from typing import List, Optional
from zipfile import ZipFile


def create_zip(output: str, files: List[str], working_directory: Optional[str] = None) -> None:
    """
    Create a zip file with a name and the given files.
    Optionally give an output path where the file should be written
    :param output: Path of the archive
    :param files: Files that should be added to the archive
    :param working_directory: set a working directory
    :return: None
    """
    path, file = os.path.split(output)
    name, extension = os.path.splitext(file)
    if extension is None or extension != ".zip":
        raise ValueError(f"Output '{output}' doesn't have 'zip' extension")
    old_cwd = os.getcwd()
    with ZipFile(Path(output), 'w') as handle:
        if working_directory:
            os.chdir(working_directory)
        for f in files:
            handle.write(f)
    os.chdir(old_cwd)

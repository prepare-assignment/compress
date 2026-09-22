import os
from pathlib import Path
from typing import List, Optional
from zipfile import ZIP_DEFLATED, ZipFile


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
    base = working_directory or ""
    # strict_timestamps=False: files from before 1980 (which zip can't store) get the date 1980-01-01
    with ZipFile(Path(output), 'w', compression=ZIP_DEFLATED, strict_timestamps=False) as handle:
        for f in files:
            # Read the file relative to the working directory, store it under the matched name. This doesn't
            # change the current directory, which wasn't restored if writing failed.
            handle.write(os.path.join(base, f), arcname=f)

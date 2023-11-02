import os.path

from prepare_toolbox.core import get_input, set_failed, set_output
from prepare_toolbox.file import get_matching_files

from prepare_compress.zip import create_zip


def compress() -> None:
    try:
        inputs = get_input("inputs", required=True)
        excluded = get_input("excluded", required=True)
        output = get_input("output", required=True)
        working_directory = get_input("working-directory")
        recursive = get_input("recursive")
        allow_outside = get_input("allow_outside_working_directory")
        files = get_matching_files(inputs, excluded, relative_to=working_directory,
                                   allow_outside_working_dir=allow_outside, recursive=recursive)
        create_zip(output, files, working_directory)
        set_output("files", files)
    except Exception as e:
        set_failed(e)


if __name__ == "__main__":
    compress()

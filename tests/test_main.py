import os
import tempfile
from pathlib import Path
from typing import List, Optional

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pytest_mock import MockerFixture

from prepare_compress.main import compress


def setup_temp(path: str) -> None:
    """
    Set up a temporary directory structure for testing
    path
    |- test.txt
    |- a.txt
    |- out
    |   |-
    |- in
    |  |- a.txt
    |  |- b.txt
    |  | nested
    |  |  | - c.txt
    :param path: path to the temporary root dir
    :return: None
    """
    out_dir = os.path.join(path, "out")
    os.mkdir(out_dir)
    Path(os.path.join(path, "test.txt")).touch()
    Path(os.path.join(path, "a.txt")).touch()
    in_dir = os.path.join(path, "in")
    os.mkdir(in_dir)
    Path(os.path.join(in_dir, "a.txt")).touch()
    Path(os.path.join(in_dir, "b.txt")).touch()
    nested_dir = os.path.join(in_dir, "nested")
    os.mkdir(nested_dir)
    Path(os.path.join(nested_dir, "c.txt")).touch()


@pytest.mark.parametrize(
    "inputs,output,working_directory,expected",
    [
        (["a.txt", "test.txt"], "archive.zip", None, ["a.txt", "test.txt"]),
        (["**/*.txt"], "archive.zip", "in", ["a.txt", "b.txt", str(Path("nested/c.txt"))]),
        (["**/*.txt"], "out/archive.zip", "in", ["a.txt", "b.txt", str(Path("nested/c.txt"))]),
    ]
)
def test_move_success(inputs: List[str],
                      output: str,
                      working_directory: Optional[str],
                      expected: List[str],
                      monkeypatch: MonkeyPatch,
                      mocker: MockerFixture) -> None:
    def __get_input(key: str, required=False):
        if key == "inputs":
            return inputs
        elif key == "output":
            return output
        elif key == "working-directory":
            return working_directory
        elif key == "allow-outside-working-directory":
            return False
        elif key == "recursive":
            return True
        return None

    mocker.patch('prepare_compress.main.get_input', side_effect=__get_input)
    spy = mocker.patch("prepare_compress.main.set_output")
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tempdir:
        monkeypatch.chdir(tempdir)
        setup_temp(tempdir)
        compress()
        assert os.path.isfile(output)
        # We need to do this otherwise it won't work on Windows......
        monkeypatch.chdir(old_cwd)
    spy.assert_called_once_with("files", expected)


def test_wrong_extension(mocker: MockerFixture, monkeypatch: MonkeyPatch) -> None:
    def __get_input(key: str, required=False):
        if key == "inputs":
            return ["a.txt"]
        elif key == "output":
            return "something/wrong"
        elif key == "working-directory":
            return None
        elif key == "allow-outside-working-directory":
            return False
        elif key == "recursive":
            return True
        return None

    mocker.patch('prepare_compress.main.get_input', side_effect=__get_input)
    spy = mocker.patch("prepare_compress.main.set_failed")
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tempdir:
        monkeypatch.chdir(tempdir)
        setup_temp(tempdir)
        compress()
        # We need to do this otherwise it won't work on Windows......
        monkeypatch.chdir(old_cwd)
    spy.assert_called_once()
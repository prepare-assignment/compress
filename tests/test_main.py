import json
import os
import zipfile
from pathlib import Path
from typing import Any, List, Optional

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pytest_mock import MockerFixture

from prepare_compress.main import compress
from prepare_compress.zip import create_zip


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


def set_inputs(monkeypatch: MonkeyPatch, **inputs: Any) -> None:
    """
    Pass the inputs like prepare-assignment core does: as JSON in PREPARE_<NAME> environment variables,
    including the defaults of task.yml. Use the names from task.yml, with '_' for '-'.
    """
    values = {"allow-outside-working-directory": False, "recursive": True, "include-hidden": False}
    values.update({key.replace("_", "-"): value for key, value in inputs.items()})
    for key, value in values.items():
        if value is not None:
            monkeypatch.setenv(f"PREPARE_{key.upper()}", json.dumps(value))


@pytest.mark.parametrize(
    "inputs,output,working_directory,expected",
    [
        (["a.txt", "test.txt"], "archive.zip", None, ["a.txt", "test.txt"]),
        (["**/*.txt"], "archive.zip", "in", ["a.txt", "b.txt", "nested/c.txt"]),
        (["**/*.txt"], "out/archive.zip", "in", ["a.txt", "b.txt", "nested/c.txt"]),
    ]
)
def test_compress_success(inputs: List[str],
                          output: str,
                          working_directory: Optional[str],
                          expected: List[str],
                          tmp_path: Path,
                          monkeypatch: MonkeyPatch,
                          mocker: MockerFixture) -> None:
    set_inputs(monkeypatch, inputs=inputs, output=output, working_directory=working_directory)
    spy = mocker.patch("prepare_compress.main.set_output")
    monkeypatch.chdir(tmp_path)
    setup_temp(str(tmp_path))
    compress()
    assert os.path.isfile(output)
    with zipfile.ZipFile(output) as archive:
        assert sorted(archive.namelist()) == expected
    spy.assert_called_once_with("files", expected)


def test_wrong_extension(tmp_path: Path, mocker: MockerFixture, monkeypatch: MonkeyPatch) -> None:
    set_inputs(monkeypatch, inputs=["a.txt"], output="something/wrong")
    spy = mocker.patch("prepare_compress.main.set_failed")
    monkeypatch.chdir(tmp_path)
    setup_temp(str(tmp_path))
    compress()
    spy.assert_called_once()


def test_outside_working_directory_not_allowed(tmp_path: Path, mocker: MockerFixture,
                                               monkeypatch: MonkeyPatch) -> None:
    (tmp_path / "project").mkdir()
    (tmp_path / "outside.txt").write_text("x")
    set_inputs(monkeypatch, inputs=["../outside.txt"], output="archive.zip")
    failed = mocker.patch("prepare_compress.main.set_failed")
    monkeypatch.chdir(tmp_path / "project")
    compress()
    failed.assert_called_once()
    assert "outside" in str(failed.call_args.args[0])


def test_outside_working_directory_allowed(tmp_path: Path, mocker: MockerFixture, monkeypatch: MonkeyPatch) -> None:
    """The input was read as 'allow_outside_working_directory', so setting it had no effect"""
    (tmp_path / "project").mkdir()
    (tmp_path / "outside.txt").write_text("x")
    set_inputs(monkeypatch, inputs=["../outside.txt"], output="archive.zip", allow_outside_working_directory=True)
    failed = mocker.patch("prepare_compress.main.set_failed")
    spy = mocker.patch("prepare_compress.main.set_output")
    monkeypatch.chdir(tmp_path / "project")
    compress()
    failed.assert_not_called()
    spy.assert_called_once_with("files", [(tmp_path / "outside.txt").as_posix()])
    assert os.path.isfile("archive.zip")


def test_archive_is_compressed(tmp_path: Path, mocker: MockerFixture, monkeypatch: MonkeyPatch) -> None:
    """The files were stored without compression (ZIP_STORED)"""
    (tmp_path / "big.txt").write_text("x" * 100_000)
    set_inputs(monkeypatch, inputs=["big.txt"], output="archive.zip")
    mocker.patch("prepare_compress.main.set_output")
    monkeypatch.chdir(tmp_path)
    compress()
    with zipfile.ZipFile("archive.zip") as archive:
        info = archive.getinfo("big.txt")
        assert info.compress_type == zipfile.ZIP_DEFLATED
        assert info.compress_size < info.file_size // 10
        assert archive.read("big.txt") == b"x" * 100_000


def test_file_before_1980(tmp_path: Path, mocker: MockerFixture, monkeypatch: MonkeyPatch) -> None:
    """Zip can't store dates before 1980, which failed the task (e.g. files from reproducible builds)"""
    (tmp_path / "old.txt").write_text("old")
    os.utime(tmp_path / "old.txt", (86400, 86400))  # 2 January 1970
    set_inputs(monkeypatch, inputs=["old.txt"], output="archive.zip")
    failed = mocker.patch("prepare_compress.main.set_failed")
    mocker.patch("prepare_compress.main.set_output")
    monkeypatch.chdir(tmp_path)
    compress()
    failed.assert_not_called()
    with zipfile.ZipFile("archive.zip") as archive:
        assert archive.getinfo("old.txt").date_time == (1980, 1, 1, 0, 0, 0)
        assert archive.read("old.txt") == b"old"


def test_working_directory_unchanged_after_error(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """create_zip changed the working directory and didn't change it back when writing failed"""
    setup_temp(str(tmp_path))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        create_zip("archive.zip", ["a.txt", "missing.txt"], "in")
    assert Path(os.getcwd()) == tmp_path


@pytest.fixture
def hidden_project(tmp_path: Path, monkeypatch: MonkeyPatch) -> Path:
    for path in [".gitignore", "README.md", "src/A.java", "src/.hidden", ".git/config"]:
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text("x")
    (tmp_path / "out").mkdir()
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _zipped(output: str) -> List[str]:
    with zipfile.ZipFile(output) as archive:
        return sorted(archive.namelist())


def test_hidden_files_not_included_by_default(hidden_project: Path, mocker: MockerFixture,
                                               monkeypatch: MonkeyPatch) -> None:
    set_inputs(monkeypatch, inputs=["**/*"], excluded=["out/**", "out"], output="out/archive.zip")
    mocker.patch("prepare_compress.main.set_output")
    compress()
    assert _zipped("out/archive.zip") == ["README.md", "src/", "src/A.java"]


def test_include_hidden(hidden_project: Path, mocker: MockerFixture, monkeypatch: MonkeyPatch) -> None:
    set_inputs(monkeypatch, inputs=["**/*"], excluded=["out/**", "out", ".git", ".git/**"], output="out/archive.zip",
               include_hidden=True)
    mocker.patch("prepare_compress.main.set_output")
    compress()
    assert _zipped("out/archive.zip") == [".gitignore", "README.md", "src/", "src/.hidden", "src/A.java"]

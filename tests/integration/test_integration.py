import contextlib
import filecmp
import os
import shutil
import socket
from unittest.mock import patch
from pathlib import Path
import pytest

# If not on Gadi, skip the tests because the test data is not available
GADI_HOSTNAME = "gadi.nci.org.au"
hostname = socket.gethostname()
# Marker to skip tests if not on Gadi
skip_marker = pytest.mark.skipif(
    not hostname.endswith(GADI_HOSTNAME),
    reason=f"Skipping integration tests because they cannot be executed on {hostname}.\n"
    "Integration tests are specifically designed to run on Gadi (gadi.nci.org.au).",
)
# Marker to suppress warnings
warning_marker = pytest.mark.filterwarnings("ignore::Warning")
# Apply the markers to all tests in this file
pytestmark = [skip_marker, warning_marker]

############################################
## === Integration tests setup === ##
############################################
TEST_DATA_DIR = Path("/g/data/vk83/testing/data/replace_landsurface/integration_tests")
INPUT_DIR = TEST_DATA_DIR / "input_data"
OUTPUT_DIR = TEST_DATA_DIR / "expected_outputs"
DRIVING_DATA_DIR = TEST_DATA_DIR / "driving_data"
# Set the ROSE_DATA environment variable to the driving data directory
os.environ["ROSE_DATA"] = str(DRIVING_DATA_DIR)
from replace_landsurface import (
    hres_ic,
)  # importing here because we need to set the ROSE_DATA env variable before importing # noqa


############################################
## === Integration tests === ##
############################################
def get_test_args(num, start, _type):
    test_dir = f"test_{num}"
    _hres_ic = (
        os.path.join(INPUT_DIR, test_dir, "hres_ic")
        if _type == "astart"
        else "NOT_USED"
    )
    return [
        "script_name",
        "--mask",
        os.path.join(INPUT_DIR, test_dir, "mask"),
        "--file",
        os.path.join(INPUT_DIR, test_dir, "file" + ".tmp"),
        "--start",
        start,
        "--type",
        _type,
        "--hres_ic",
        _hres_ic,
    ]


@pytest.fixture
def mock_sys_argv():
    @contextlib.contextmanager
    def _mock_sys_argv(num, start, _type):
        with patch("sys.argv", get_test_args(num, start, _type)):
            yield mock_sys_argv

    return _mock_sys_argv


@pytest.fixture()
def get_error_msg():
    def _get_error_msg(num, output, expected_output):
        return f"Test {num}: Test output '{output}' does not match the expected output '{expected_output}'!"

    return _get_error_msg


@pytest.fixture(scope="module")
def working_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("replace_landsurface_integration_tests")


@pytest.fixture()
def get_output_path(working_dir):
    def _get_output_path(num):
        return os.path.join(working_dir, f"output_{num}")

    return _get_output_path


@pytest.fixture()
def get_expected_output_path():
    def _get_expected_output_path(num):
        return os.path.join(OUTPUT_DIR, f"output_{num}")

    return _get_expected_output_path


# Set the ROSE_DATA environment variable to the driving data directory in all tests
@pytest.fixture(autouse=True)
def mock_rose_data(monkeypatch):
    monkeypatch.setenv("ROSE_DATA", DRIVING_DATA_DIR)


@pytest.fixture(scope="module")
def original_shutil_move():
    return shutil.move


@pytest.fixture()
def new_shutil_move(original_shutil_move, get_output_path, get_expected_output_path):
    def _new_shutil_move(num):
        def _wrapper(src, dst, **kwargs):
            output_path = get_output_path(num)
            return original_shutil_move(src=src, dst=output_path, **kwargs)

        return _wrapper

    return _new_shutil_move


@pytest.mark.parametrize(
    "num, start, _type",
    [
        (1, "202202260000", "era5land"),
        (2, "202008090000", "barra"),
        (3, "202112310000", "astart"),
    ],
    ids=[
        "hres_ic_era5land",
        "hres_ic_barra",
        "hres_ic_astart",
    ],
)
def test_hres_ic(
    new_shutil_move,
    get_output_path,
    get_expected_output_path,
    get_error_msg,
    mock_sys_argv,
    num,
    start,
    _type,
):
    """
    Test the hres_ic entry point
    """
    with mock_sys_argv(num, start, _type):
        with patch("shutil.move", side_effect=new_shutil_move(num)):
            hres_ic.main()
    output = get_output_path(num)
    expected_output = get_expected_output_path(num)
    # Compare the output file with the expected output
    assert filecmp.cmp(output, expected_output), get_error_msg(
        num, output, expected_output
    )

@pytest.mark.parametrize(
    "num, start, _type",
    [
        (4, "202305040000", "era5land"),
        # (5, "202403050000", "barra"),
    ],
    ids=[
        "hres_eccb_era5land", 
        # "hres_eccb_barra",
    ],
)
def test_hres_eccb(
    new_shutil_move,
    get_output_path,
    get_expected_output_path,
    get_error_msg,
    mock_sys_argv,
    num,
    start,
    _type,
):
    """
    Test the hres_eccb entry point
    """
    with mock_sys_argv(num, start, _type):
        with patch("shutil.move", side_effect=new_shutil_move(num)):
            hres_ic.main()
    output = get_output_path(num)
    expected_output = get_expected_output_path(num)
    # Compare the output file with the expected output
    assert filecmp.cmp(output, expected_output), get_error_msg(
        num, output, expected_output
    )
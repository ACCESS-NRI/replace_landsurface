import filecmp
import os
import pytest
import shutil
import socket
import tempfile
from unittest.mock import patch
from datetime import datetime

# If not on Gadi, fail the test because the test data is not available
GADI_HOSTNAME = "gadi.nci.org.au"
hostname = socket.gethostname()
if not hostname.endswith(GADI_HOSTNAME):
    raise EnvironmentError(
        f"Test not supported to be run on {hostname}. This test must be run on Gadi (gadi.nci.org.au)."
    )

############################################
## === Integration tests setup === ##
############################################
print("\n## === Integration tests setup started === ##")
TEST_DATA_DIR = '/g/data/vk83/testing/data/replace_landsurface/integration_tests'
INPUT_DIR = os.path.join(TEST_DATA_DIR,'input_data')
OUTPUT_DIR = os.path.join(TEST_DATA_DIR,'expected_outputs')
DRIVING_DATA_DIR = os.path.join(TEST_DATA_DIR,'driving_data')
# Set the ROSE_DATA environment variable to the driving data directory
os.environ["ROSE_DATA"] = "/g/data/vk83/testing/data/replace_landsurface/integration_tests/driving_data"
from replace_landsurface import hres_ic # importing here because we need to set the ROSE_DATA env variable before importing # noqa

# Set up working directory path'
working_dir_prefix='replace_landsurface_integration_tests_'
working_dir_date=datetime.now().strftime("%Y%m%d%H%M%S")
WORKING_DIR = os.path.join(tempfile.gettempdir(), working_dir_prefix + working_dir_date)
# Copy input data to the working directory
shutil.copytree(INPUT_DIR, WORKING_DIR)
# Change current working directory to the working directory
os.chdir(WORKING_DIR)
print("## === Integration tests setup complete! === ##")
############################################
## === Integration tests === ##
############################################
# Suppress warnings
pytestmark = pytest.mark.filterwarnings("ignore::Warning")

def get_error_msg(num, output, expected_output):
    return f"Test {num}: Test output '{output}' does not match the expected output '{expected_output}'!"
# Define the command-line arguments for the tests
def get_test_args(num, start, _type):
    test_dir = f'test_{num}'
    _hres_ic = os.path.join(WORKING_DIR,test_dir,'hres_ic') if _type == 'astart' else 'NOT_USED'
    return [
        "script_name",
        '--mask',
        os.path.join(WORKING_DIR,test_dir,'mask'),
        '--file',
        os.path.join(WORKING_DIR,test_dir,'file'+'.tmp'),
        '--start',
        start,
        '--type',
        _type,
        '--hres_ic',
        _hres_ic,
    ]

def get_output_path(num):
    return os.path.join(WORKING_DIR,f'test_{num}','file')

def get_expected_output_path(num):
    return os.path.join(OUTPUT_DIR,f'output_{num}')

# Set the ROSE_DATA environment variable to the driving data directory in all tests
@pytest.fixture(autouse=True)
def mock_rose_data(monkeypatch):
    monkeypatch.setenv("ROSE_DATA", DRIVING_DATA_DIR)

@patch("sys.argv", get_test_args(1,'202202260000','era5land'))
def test_hres_ic_era5land():
    """
    Test the hres_ic entry point with '--type era5land'
    """
    num=1
    hres_ic.main()
    output = get_output_path(num)
    expected_output = get_expected_output_path(num)
    # # Compare the output file with the expected output
    assert filecmp.cmp(output, expected_output), get_error_msg(num, output, expected_output)

@patch("sys.argv", get_test_args(2,'202008090000','barra'))
def test_hres_ic_barra():
    """
    Test the hres_ic entry point with '--type barra'
    """
    num=2
    hres_ic.main()
    output = get_output_path(num)
    expected_output = get_expected_output_path(num)
    # # Compare the output file with the expected output
    assert filecmp.cmp(output, expected_output), get_error_msg(num, output, expected_output)

@patch("sys.argv", get_test_args(3,'202112310000','astart'))
def test_hres_ic_astart():
    """
    Test the hres_ic entry point with '--type astart'
    """
    num=3
    hres_ic.main()
    output = get_output_path(num)
    expected_output = get_expected_output_path(num)
    # # Compare the output file with the expected output
    assert filecmp.cmp(output, expected_output), get_error_msg(num, output, expected_output)

def test_hres_eccb_era5land():
    """
    Test the hres_eccb entry point with '--type era5land'
    """
    pass

def test_hres_eccb_barra():
    """
    Test the hres_eccb entry point with '--type barra'
    """
    pass
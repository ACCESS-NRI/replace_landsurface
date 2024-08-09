import pytest
from unittest.mock import patch
from pathlib import Path

# TODO: place ROSE DATA into a function (or an input argument) so it doesn't need to get called when importing the module
import os
os.environ['ROSE_DATA'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'test_data/rose_data')

# TODO: Turn src into a package so that we can import the function directly
# For now required to import from src
import sys #To delete when src is a package
srcpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'src') #To delete when src is a package
sys.path.insert(0,srcpath) #To delete when src is a package

from hres_ic import get_start_time, replace_input_file_with_tmp_input_file, parse_arguments

del sys.path[0] #To delete when src is a package

def test_get_start_time():
    time = "199205041155"
    assert get_start_time(time) == "19920504T1155Z"

def test_replace_input_file_with_tmp_input_file():
    tmppath = Path('example/of/.tmp/file.tmp')
    newpath = Path('example/of/.tmp/file')
    # Mock the shutil.move function
    with patch('shutil.move') as mock_move:
        replace_input_file_with_tmp_input_file(tmppath)
        mock_move.assert_called_once_with(tmppath,newpath)

def test_replace_input_file_with_tmp_input_file_fail():
    tmppath = Path('example/of/.tmp/invalid/filetmp')
    # Mock the shutil.move function
    with patch('shutil.move'):
        with pytest.raises(ValueError):
            replace_input_file_with_tmp_input_file(tmppath)

@patch('sys.argv', ['program_name', '--mask', 'mask_path', '--file', 'file_path', '--start', '202408121230'])
def test_parse_arguments_success():
    args = parse_arguments()
    assert args.mask == Path('mask_path')
    assert args.file == Path('file_path')
    assert args.start == '202408121230'
    assert args.type == 'era5land'

@patch('sys.argv', ['program_name', '--mask', 'mask_path', '--file', 'file_path', '--start', '202408121230', '--type', 'newtype'])
def test_parse_arguments_with_type():
    args = parse_arguments()
    assert args.type == 'newtype'

@patch('sys.argv', ['program_name', '--file', 'file_path', '--start', '2024-08-12'])
def test_parse_arguments_missing_mask():
    with pytest.raises(SystemExit):
        parse_arguments()

@patch('sys.argv', ['program_name', '--mask', 'mask_path', '--start', '2024-08-12'])
def test_parse_arguments_missing_file():
    with pytest.raises(SystemExit):
        parse_arguments()

@patch('sys.argv', ['program_name', '--mask', 'mask_path', '--file', 'file_path'])
def test_parse_arguments_missing_start():
    with pytest.raises(SystemExit):
        parse_arguments()
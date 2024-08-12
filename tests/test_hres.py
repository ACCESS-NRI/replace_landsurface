import pytest
from unittest.mock import patch, Mock
from pathlib import Path

# TODO: place ROSE DATA into a function (or an input argument) so it doesn't need to get called when importing the module
import os
os.environ['ROSE_DATA'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'test_data/rose_data')

# TODO: Turn src into a package so that we can import the function directly
# For now required to import from src
import sys #To delete when src is a package
srcpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'src') #To delete when src is a package
sys.path.insert(0,srcpath) #To delete when src is a package

from hres_ic import get_start_time, replace_input_file_with_tmp_input_file, parse_arguments, set_replace_function, main

del sys.path[0] #To delete when src is a package

# Test get_start_time
def test_get_start_time():
    time = "199205041155"
    assert get_start_time(time) == "19920504T1155Z"

# Test replace_input_file_with_tmp_input_file
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

# Test parse_arguments
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

@patch('sys.argv', ['program_name', '--file', 'file_path', '--start', '202408121230'])
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

# Test set_replace_function
@patch('replace_landsurface_with_ERA5land_IC.swap_land_era5land')
def test_set_replace_function_era5land(mock_era5land):
    result = set_replace_function("era5land")
    assert result == mock_era5land

@patch('replace_landsurface_with_BARRA2R_IC.swap_land_barra')
def test_set_replace_function_barra(mock_barra):
    result = set_replace_function("barra")
    assert result == mock_barra

def test_set_replace_function_unknown():
    result = set_replace_function("unknown")
    assert result is None

# Test main function
@patch('hres_ic.parse_arguments')
@patch('hres_ic.get_start_time')
@patch('hres_ic.set_replace_function')
@patch('hres_ic.replace_input_file_with_tmp_input_file')
def test_main_with_replacement(mock_replace_input, mock_set_replace, mock_get_start, mock_parse_args):
    # Mock the arguments returned by parse_arguments
    mock_args = Mock()
    mock_args.mask = "mock_mask"
    mock_args.file = "mock_file"
    mock_args.start = "mock_start"
    mock_args.type = "era5land"
    mock_parse_args.return_value = mock_args
    
    # Mock the return value of get_start_time
    mock_get_start.return_value = "mock_time"
    
    # Mock the replacement function
    mock_replace_func = Mock()
    mock_set_replace.return_value = mock_replace_func
    
    main() 
    mock_parse_args.assert_called_once()
    mock_get_start.assert_called_once_with("mock_start")
    mock_set_replace.assert_called_once_with("era5land")
    mock_replace_func.assert_called_once_with("mock_mask", "mock_file", "mock_time")
    mock_replace_input.assert_called_once_with("mock_file")

@patch('hres_ic.parse_arguments')
@patch('hres_ic.get_start_time')
@patch('hres_ic.set_replace_function')
@patch('hres_ic.replace_input_file_with_tmp_input_file')
def test_main_without_replacement(mock_replace_input, mock_set_replace, mock_get_start, mock_parse_args):
    # Mock the arguments returned by parse_arguments
    mock_args = Mock()
    mock_args.mask = "mock_mask"
    mock_args.file = "mock_file"
    mock_args.start = "mock_start"
    mock_args.type = "unknown_type"
    mock_parse_args.return_value = mock_args
    
    # Mock the return value of get_start_time
    mock_get_start.return_value = "mock_time"
    
    # Mock the replacement function to return None
    mock_set_replace.return_value = None
    
    main()
    mock_parse_args.assert_called_once()
    mock_get_start.assert_called_once_with("mock_start")
    mock_set_replace.assert_called_once_with("unknown_type")
    mock_replace_input.assert_not_called()  # Should not be called since replace_function is None
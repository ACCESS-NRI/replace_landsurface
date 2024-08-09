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

from hres_ic import get_start_time, replace_input_file_with_tmp_input_file

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
    with patch('shutil.move') as mock_move:
        with pytest.raises(ValueError):
            replace_input_file_with_tmp_input_file(tmppath)
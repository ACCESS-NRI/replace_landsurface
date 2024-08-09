import pytest
from unittest.mock import patch

# TODO: place ROSE DATA into a function (or an input argument) so it doesn't need to get called when importing the module
import os
os.environ['ROSE_DATA'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'test_data/rose_data')

# TODO: Turn src into a package so that we can import the function directly
# For now required to import from src
import sys #To delete when src is a package
srcpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'src') #To delete when src is a package
sys.path.insert(0,srcpath) #To delete when src is a package

from replace_landsurface_with_ERA5land_IC import bounding_box

del sys.path[0] #To delete when src is a package

# Make this directory a proper Python package
# This file was created by fix_imports.py to fix relative import issues

import os
import sys

# Add the current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
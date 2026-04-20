"""Deprecated - use data.r2_storage instead."""
import warnings
warnings.warn("r2.py is deprecated, use data.r2_storage instead", DeprecationWarning, stacklevel=2)

from data.r2_storage import *

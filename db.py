"""Deprecated - use data.mongodb_repository instead."""
import warnings
warnings.warn("db.py is deprecated, use data.mongodb_repository instead", DeprecationWarning, stacklevel=2)

from data.mongodb_repository import *

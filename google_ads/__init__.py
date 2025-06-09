"""Compatibility package mapping to google_ads_mcp_server.google_ads."""
# flake8: noqa
import importlib
import sys
from types import ModuleType
from pathlib import Path

_real_pkg = importlib.import_module('google_ads_mcp_server.google_ads')
module = ModuleType('google_ads')
module.__dict__.update({'__file__': __file__, '__path__': [str(Path(_real_pkg.__file__).resolve().parent)]})

sys.modules[__name__] = module

def __getattr__(name):
    full = f'google_ads_mcp_server.google_ads.{name}'
    mod = importlib.import_module(full)
    sys.modules[f'{__name__}.{name}'] = mod
    return mod

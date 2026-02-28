"""Cython build script — compile license/*.py to native extensions.

Usage:
    python license/setup_cython.py build_ext --inplace

This compiles fingerprint.py, token_store.py, and validator.py into
.so (macOS/Linux) or .pyd (Windows) files that cannot be decompiled.
"""

from setuptools import setup
from Cython.Build import cythonize
from Cython.Compiler import Options

Options.annotate = False

setup(
    name="aihunter_license",
    packages=[],  # Suppress automatic package discovery
    ext_modules=cythonize(
        [
            "license/fingerprint.py",
            "license/token_store.py",
            "license/validator.py",
            "license/settings_store.py",
        ],
        compiler_directives={
            "language_level": "3",
            "embedsignature": False,
            "optimize.use_switch": True,
        },
        annotate=False,
    ),
)

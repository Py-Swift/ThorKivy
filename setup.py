#!/usr/bin/env python3
"""
setup.py for ThorKivy — Cython extensions that cimport Kivy's Instruction
and render ThorVG shapes via GlCanvas into Kivy's GL pipeline.
"""
import os
import sys
from pathlib import Path

from setuptools import Extension, find_packages, setup
from Cython.Build import cythonize

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
#  Kivy include paths (for cimport + gl_redirect.h)
# ---------------------------------------------------------------------------
import kivy

KIVY_DIR = Path(kivy.__file__).resolve().parent
KIVY_INCLUDE = str(KIVY_DIR / "include")

# ---------------------------------------------------------------------------
#  Extension
# ---------------------------------------------------------------------------
extra_compile_args = ["-std=c++14"]
if sys.platform == "darwin":
    extra_compile_args.append(
        f"-mmacosx-version-min={os.environ.get('MACOSX_DEPLOYMENT_TARGET', '11.0')}"
    )

ext_modules = cythonize(
    [
        Extension(
            name="thorkivy.instructions",
            sources=["src/thorkivy/instructions.pyx"],
            include_dirs=[KIVY_INCLUDE],
            extra_compile_args=extra_compile_args,
            language="c++",
        ),
    ],
    compiler_directives={
        "language_level": "3",
        "boundscheck": False,
        "wraparound": False,
    },
)

setup(
    ext_modules=ext_modules,
)

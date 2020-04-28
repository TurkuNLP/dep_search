import os
from setuptools import setup, Extension
from Cython.Build import cythonize

setup(
    name="dep_search",
    version="0.1.0",
    author="J. Luotolahti, J. Kanerva, S. Pyysalo, F. Ginter",
    description="Search engine for querying copora of dependency trees",
    classifiers=[
        'Programming Language :: Python :: 3'
    ],
    setup_requires=["cython"],
    ext_modules=cythonize(["dep_search/*.pyx", "dep_search/setlib/*.pyx"]),
    packages=["dep_search", "api_gui"],
    install_requires=[
        "plyvel",
        "ply",
        "pysolr",
        "flask",
        "lmdb",
    ]
)

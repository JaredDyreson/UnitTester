from setuptools import setup

PKG_NAME = "UnitTester"

setup(
    name=PKG_NAME,
    install_requires=[
        'wheel',
        'termcolor'
    ],
    scripts=[
        'scripts/muffin_top'
    ]
)

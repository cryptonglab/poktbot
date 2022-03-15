import sys
from setuptools import setup, setuptools

from poktbot import __version__


def readme():
    with open('README.md', encoding="UTF-8") as f:
        return f.read()


if sys.version_info < (3, 4, 1):
    sys.exit('Python < 3.4.1 is not supported!')


setup(
    name='poktbot',
    version=__version__,
    description='Pocket telegram bot for handling nodes tracking information and stats',
    long_description_content_type="text/markdown",
    long_description=readme(),
    packages=setuptools.find_packages(exclude=["tests.*", "tests"]),
    url='https://github.com/cryptonglab/poktbot',
    install_requires=[
        "Telethon==1.10.8",
        "pandas==1.3.5",
        "numpy==1.21.5",
        "pyyaml==6.0",
        "joblib==1.1.0",
        "lz4==4.0.0",
        "bokeh==2.4.2",
        "XlsxWriter==3.0.3",
        "openpyxl==3.0.9",
        "plotly==5.6.0",
        "requests==2.27.1",
        "matplotlib==3.5.1",
        "selenium==4.1.0"
    ],
    classifiers=[],
    test_suite='nose.collector',
    tests_require=['nose'],
    include_package_data=True,
    keywords="pocket bot telegram cryptocurrency nodes information tracking managing system".split(" "),
    zip_safe=False,
    entry_points={
        'console_scripts': ['poktbot=poktbot.main:main'],
    }
)

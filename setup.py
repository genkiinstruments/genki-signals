import re
import setuptools


# Hacky way to get the version string from the __init__ file, can't import it since it hasn't been "built" yet
VERSIONFILE="genki_signals/__init__.py"
getversion = re.search( r"^__version__ = ['\"]([^'\"]*)['\"]", open(VERSIONFILE, "rt").read(), re.M)
if getversion:
    version = getversion.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

short_description = "A library for realtime signal processing and machine learning"
long_description = open("README.md").read()

setuptools.setup(
    name="genki_signals",
    version=version,
    description=short_description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    license_files=["LICENSE"],
    url="https://github.com/genkiinstruments/genki-signals",
    python_requires='>=3.9',
    install_requires=[
        "numpy",
        "pandas",
        "scipy",
        "onnx",
        "onnxruntime",
        "opencv-python",
        "pynput",
        "bqplot",
        "ipywidgets",
        "IPython",
        "ahrs",
        "imufusion",
        "bleak",
        "genki_wave",
    ],
    author="Genki Instruments",
    author_email="genki@genkiinstruments.com",
    keywords = ["Signal Processing", "Machine Learning", "Realtime"],
    packages=setuptools.find_packages(exclude=("tests", "examples")),
    classifiers = [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)

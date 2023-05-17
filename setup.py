import setuptools

version = (0, 1, 0)
__version__ = ".".join(map(str, version))

short_description = "A library for realtime signal processing and machine learning"
long_description = open("README.md").read()

setuptools.setup(
    name="genki_signals",
    version=__version__,
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
        "bqplot",
        "ipywidgets",
        "ahrs",
        "imufusion",
        "bleak",
        "genki_wave",
    ],
    author="Genki Instruments",
    author_email="genki@genkiinstruments.com",
    keywords = ["Signal Processing", "Machine Learning", "Realtime"],
    classifiers = [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
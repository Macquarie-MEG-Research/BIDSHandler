import setuptools

VERSION = "0.1.1"

DESCRIPTION = "API for handling BIDS compatible data"
DOWNLOAD_URL = "https://github.com/Macquarie-MEG-Research/BIDSHandler"
LONG_DESCRIPTION = open('README.md').read()

setuptools.setup(
    name="BIDSHandler",
    version=VERSION,
    author="Matt Sanderson",
    author_email="matt.sanderson@mq.edu.au",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    include_package_data=True,
    download_url=DOWNLOAD_URL,
    packages=setuptools.find_packages(),
    install_requires=['pandas'],
    license="MIT",
    platform="any",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

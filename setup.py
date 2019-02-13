import setuptools

VERSION = "0.3dev0"

DESCRIPTION = "Simple way to manage and manipulate BIDS compatible data"
DOWNLOAD_URL = "https://github.com/Macquarie-MEG-Research/BIDSHandler"
DOC_URL = "https://macquarie-meg-research.github.io/BIDSHandler/"
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
    license="MIT",
    platform="any",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    project_urls={"Documentation": DOC_URL}
)

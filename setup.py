import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="phy_sx127x",
    version="0.0.1",
    author="Dean Hall",
    author_email="dwhall256@gmail.com",
    description="A physical layer (PHY) driver for the Semtech SX127x radio data modem",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dwhall/phy_sx127x",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: OSI Approved :: MIT License",

        # Python 3.4 or later because asyncio is required
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        # Alpha status because there is API breakage between releases
        # without changing the major version number
        'Development Status :: 3 - Alpha',

        # This project is designed to run on a Raspberry Pi
        # with a SX127X LoRa radio attached via the SPI bus
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Hardware :: Hardware Drivers",

        # This project may be of interest to amateur radio operators,
        # but can be adapted to ISM frequencies for non-licensed persons.
        "Topic :: Communications :: Ham Radio",
    ],
)

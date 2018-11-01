import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="HeyMac",
    version="0.1.0",
    author="Dean Hall",
    author_email="dwhall256@gmail.com",
    description="Layered protocol driver for low-power, lossy wireless data transfer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dwhall/HeyMac",
    packages=setuptools.find_packages(),
    scripts = ["scripts/heymac_gen_identity.py"],
    classifiers=[
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",

        # This project is designed to run on a Raspberry Pi
        # with a SX127X LoRa radio attached via the SPI bus
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Topic :: Communications :: Ham Radio",
    ],
)

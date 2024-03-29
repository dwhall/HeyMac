import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="HeyMac",
    version="0.1.2",
    author="Dean Hall",
    author_email="dwhall256@gmail.com",
    description="A small, flexible protocol stack for the Semtech SX127x radio data modem.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dwhall/HeyMac",
    packages=setuptools.find_packages(),
    scripts=["scripts/heymac_gen_creds.py"],
    python_requires=">=3.5",
    classifiers=[
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",

        # This project is designed to run on a Raspberry Pi
        # with a SX127x LoRa radio attached via the SPI bus
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Topic :: Communications :: Ham Radio",
    ],
)

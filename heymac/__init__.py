import sys

# On linux/raspi, import normal GPIO and serial modules
if sys.platform == "linux":
    import RPi.GPIO as GPIO
    import serial

# Provide mock modules to non-linux platforms to allow incomplete execution
else:
    import mock_gpio as GPIO
    import mock_serial as serial

from .mac_cmds import *
from .mac_frame import *
from .net_frame import *
from .trn_udp import *

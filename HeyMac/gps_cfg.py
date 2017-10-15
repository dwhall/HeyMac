class GpsCfg(object):
    pass


class DraginoLoraGpsHat(GpsCfg):
    # WIRING REQUIREMENT: connect GPS module's PPS pin 6 to RPi's GPIO26 pin 37
    serial_port = "/dev/serial0"
    serial_baud = 9600
    pps_chnl    = 26

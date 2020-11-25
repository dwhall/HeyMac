# This file lets the project run on a PC,
# but does no real action on hardware.
class SpiDev(object):
    def close(self,): pass
    def open(self, port, cs): pass
    def xfer2(self, b):
        # If REG_VERSION, return CHIP_VERSION
        if b[0] == 0x42 and len(b) == 2:
            return [0, 18]
        # If REG_RDO_OPMODE, return STBY
        elif b[0] == 0x01 and len(b) == 2:
            return [0, 1]
        else:
            return [0,]*len(b)

class SpiDev(object):
    def close(self,): pass
    def open(self, port, cs): pass
    def xfer2(self, b): 
        # If REG_VERSION, return CHIP_VERSION
        if b[0] == 0x42 and len(b) == 2:
            return [0, 18]
        else:
            return [0,]*len(b)

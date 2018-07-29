class SpiDev(object):
    def close(self,): pass
    def open(self, port, cs): pass
    def xfer2(self, b): return [0,]*len(b)
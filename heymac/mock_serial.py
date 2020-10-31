class Serial(object):
    def __init__(self, port, baudrate, timeout): self.baudrate = baudrate
    def read(self, n): return [0,]*n
    def close(self): pass

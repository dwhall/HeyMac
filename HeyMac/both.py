import asyncio

from gps import GpsAhsm
from ahsm import HeyMac


if __name__ == "__main__":
    gps = GpsAhsm(GpsAhsm.initial)
    gps.start(0)

    m = HeyMac()
    m.start(0)

    loop = asyncio.get_event_loop()
    loop.run_forever()
    loop.close()

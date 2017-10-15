import asyncio

import ahsm, gps, gps_cfg


if __name__ == "__main__":
    gps = gps.GpsAhsm(gps_cfg.DraginoLoraGpsHat)
    gps.start(0)

    m = ahsm.HeyMac()
    m.start(0)

    loop = asyncio.get_event_loop()
    loop.run_forever()
    loop.close()

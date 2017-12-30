import asyncio

import phy_gpio_ahsm, phy_spi_ahsm, phy_uart_ahsm


if __name__ == "__main__":
    # Start state machines
    gpioAhsm = phy_gpio_ahsm.GpioAhsm(phy_gpio_ahsm.GpioAhsm.initial)
    spiAhsm = phy_spi_ahsm.SX127xSpiAhsm(phy_spi_ahsm.SX127xSpiAhsm.initial)
    uartAhsm = phy_uart_ahsm.UartAhsm(phy_uart_ahsm.UartAhsm.initial)

    gpioAhsm.start(0)
    spiAhsm.start(0)
    uartAhsm.start(0)

    # Start event loop
    loop = asyncio.get_event_loop()
    loop.run_forever()
    loop.close()

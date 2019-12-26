"""Project-level physical configuration.

Note: Configuration items are things that are hard-wired.
If configuration were to change during runtime, the software should reset.

This files contains RaspberryPi GPIO pin information.
"""


try:
    import RPi.GPIO as GPIO
except:
    from heymac import mock_gpio as GPIO


# This configuration is for the Dragino LoRa GPS Hat v1.3
# with extra connections for GPS and DIO3-5 made by the author
gpio_ins = (
    #pin_nmbr, pin_edge, sig_name
    (4, GPIO.RISING, "PHY_DIO0"),
    (23, GPIO.RISING, "PHY_DIO1"),
    (24, GPIO.RISING, "PHY_DIO2"),
    (6, GPIO.RISING, "PHY_DIO3"),
    (5, GPIO.RISING, "PHY_DIO4"),
#    (22, GPIO.RISING, "PHY_DIO5"),
    (26, GPIO.RISING, "PHY_GPS_PPS"),
)

gpio_outs = (
    #pin_nmbr, pin_initial
    (17, GPIO.HIGH), # GPS_RST
)

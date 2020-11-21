phy_sx127x
==========

Introduction
------------

A physical layer (PHY) driver for the `Semtech SX127x family`_
of radio data transceivers written in Python3
using the `farc`_ state machine framework and meant to run on
Linux on a Raspberry Pi 3 with a modified `Dragino LoRa GPS Hat`_

A state machine manages the operational behavior and calls into a PHY layer module
to interact with the radio via the SPI bus and GPIO pins.
This software takes advantage of advanced features of the SX127x,
so connection to DIO pins 1,2,3 and 5 is necessary.

This repository is designed to be a git submodule
so that it may be re-used by multiple projects
and is not operational on its own.

.. _`Semtech SX127x family`: https://www.semtech.com/products/wireless-rf/lora-transceivers/sx1276
.. _`farc`: https://github.com/dwhall/farc
.. _`Dragino LoRa GPS Hat`: https://wiki.dragino.com/index.php?title=Lora/GPS_HAT


Software
--------

phy_sx127x_ahsm.py
    Contains PhySX127xAhsm, the PHY layer state machine that automates
    the behavior of the Semtech SX127x family of radio transceivers.

phy_sx127x.py
    Contains PhySX127x, the PHY layer SPI operations, settings management
    and GPIO interfaces for the Semtec SX127x family of digital radio transceivers.


State Machine
-------------

After initialization, the behavior of the state machine (SM) is
to run in a loop that applies settings and then performs an action.
The action is to transmit, listen or sleep.
The SM maintains a transmit queue and a boolean variable
that it uses decide what action to take.
If the transmit queue is empty, the variable determines
whether to listen or sleep.
If the queue is not empty, the next item in the queue
will be transmitted.  After the transmission, operation proceeds
to the Setting state and the entire process repeats.
But the Sleeping and Listening states are slightly different.
The SM remains sleeping or listening until some event arrives
that requires attention (for example, a new item in the transmit
queue or a new setting needs to be applied).

One other thing to mention is that the Listening state turns
on the radio receiver, but only the reception of a valid
header will cause the transition to the Rxing state.
The Rxing state exists to keep the radio in receive
mode until reception is done or there is a timeout.
We wouldn't want, for example, the arrival of a new item
in the transmit queue to cause a state transition that
would turn off the receiver in the middle of a reception.

There are many more details to the SM's operation.
But that is the gist of it.  See the code for details.
Likewise, the diagram below shows the important aspects of the
SM, but it does not capture all details.

.. image:: docs/PhySX127xAhsm.png


Public Interface
----------------

This section describes the public interface of the PHY layer,
which is the set of methods and arguments available to the entity
that instantiates the PHY layer.

======================  ================================================
Method                  Description
======================  ================================================
``PhySX127xAhsm()``     The constructor accepts one argument.

                        - *lstn_by_dflt* selects the default behavior
                          when the device is not doing anything else.
                          If lstn_by_dflt is ``True``, then the device turns
                          on its receiver; if it is ``False``, the device
                          is put into low-power sleep mode.
----------------------  ------------------------------------------------
``enqueue_for_tx()``    Puts a set of data into the transmit queue.

                        - *tx_bytes* The Python ``bytes`` object
                          containing the literal payload to transmit.
                        - *tx_time* A number representing the time
                          to perform the transmit.  This is either an
                          absolute value for time (using the same time as
                          ``farc.Framework._event_loop.time()``); or it is
                          a special value:

                          * ``PhySX127xAhsm.ENQ_TM_NOW``
                          * ``PhySX127xAhsm.ENQ_TM_IMMEDIATELY``

                          ``ENQ_TM_NOW`` uses the current ``time()`` and
                          inserts this transmission into queue (where there
                          may be other, potentially delayed payloads waiting).
                          ``ENQ_TM_IMMEDIATELY`` bypasses the normal queue
                          and puts the payload in an immediate queue.
                          The immediate queue is exhausted before the
                          normal queue may transmit.  Use ``ENQ_TM_IMMEDIATELY``
                          sparingly.

                        - *tx_stngs* is a sequence of ``(name, value)``
                          pairs specifically for transmission.
                          See `Settings`_ for more details.
----------------------  ------------------------------------------------
``set_dflt_stngs()``    Sets the default PHY settings.

                        - *dflt_stngs* is a sequence of ``(name, value)``
                          pairs.  This should be called once before the
                          state machine is started.  See `Settings`_
                          for more details.
----------------------  ------------------------------------------------
``start_stack()``       Starts the PHY layer state machine with the
                        given ``farc.Ahsm`` priority.
======================  ================================================


Settings
--------

An important aspect of manipulating the PHY layer is applying settings
to the device.  PhySX127x makes applying device settings easy for you.
Instead of dealing with register addresses, bitwise operations and
SPI transfers, all you have to do is set a field to a value.
The field is a bit field, but you only need to know its name.
**With one exception**, the value you use is exactly the value that would
go into the bit field (you don't do any shifting).  The exception is
the radio frequency setting, "FLD_RDO_FREQ", in which case you give
the desired frequency in Hertz.  Here are some examples::

    # Set the frequency to 432.550 Mhz
    set_fld("FLD_RDO_FREQ", 432550000)

    # Set the LoRa Coding Rate to 4:5
    set_fld("FLD_LORA_CR", 1)

    # Set the LoRa Spread Factor to 128 chips per sec
    set_fld("FLD_LORA_SF", phy_sx127x.PhySX127x.STNG_LORA_SF_128_CPS)

If you have a batch of settings to apply, put the (name, value) tuples
into a sequence and call set_flds().::

    set_flds((
        ("FLD_RDO_FREQ", 432550000),
        ("FLD_LORA_CR", 1),
        ("FLD_LORA_SF", phy_sx127x.PhySX127x.STNG_LORA_SF_128_CPS),
    ))

PhySX127x does not write these values to the device registers immediately.
Instead, it keeps the data until PhySX127xAhsm enters a safe state when the
radio is not busy.  PhySX127x is also a little smart: it only writes values
that have changed.  This keeps SPI traffic down.

Now all you need is the list of field names.
Consult the `SX127x datasheet`_ to learn what these fields do:

==========================  ==================  ==================  ==================
Field name                  Min value           Max Value           Value after reset
==========================  ==================  ==================  ==================
"FLD_RDO_FREQ"              137000000           1020000000          434000000
--------------------------  ------------------  ------------------  ------------------
"FLD_RDO_LF_MODE"           0                   1                   1
"FLD_RDO_LORA_MODE"         0                   1                   0
"FLD_RDO_OUT_PWR"           0                   15                  15
"FLD_RDO_MAX_PWR"           0                   7                   4
"FLD_RDO_PA_BOOST"          0                   1                   0
"FLD_RDO_LNA_BOOST_HF"      0                   3                   0
"FLD_RDO_LNA_GAIN"          1                   6                   1
"FLD_RDO_DIO0"              0                   2                   0
"FLD_RDO_DIO1"              0                   2                   0
"FLD_RDO_DIO2"              0                   2                   0
"FLD_RDO_DIO3"              0                   2                   0
"FLD_RDO_DIO4"              0                   2                   0
"FLD_RDO_DIO5"              0                   2                   0
"FLD_LORA_IMPLCT_HDR_MODE"  0                   1                   0
"FLD_LORA_CR"               1                   4                   1
"FLD_LORA_BW"               0                   9                   7
"FLD_LORA_CRC_EN"           0                   1                   0
"FLD_LORA_SF"               6                   12                  7
"FLD_LORA_RX_TMOUT"         0                   1023                0
"FLD_LORA_PREAMBLE_LEN"     0                   65535               0
"FLD_LORA_AGC_ON"           0                   1                   0
"FLD_LORA_SYNC_WORD"        0                   255                 18
==========================  ==================  ==================  ==================

.. _`SX127x datasheet`: https://www.semtech.com/products/wireless-rf/lora-transceivers/sx1276#download-resources


Hardware
--------

The prototype platform is a `Raspberry Pi 3 Model B`_
with a `Dragino LoRa/GPS Hat`_ that I bought `on Tindie`_.
They sent me version 1.3 of the PCB eventhough there are later versions.
So I had to make a couple fixes and a few additions.  The first and most
important fix is to connect the radio's SPI Chip Select (CS) signal to the Pi's
SPI0 CS0.  Without that, you have to programmatically control the radio's CS
before and after every transaction (that's a PITA that slows hardware and
software).  It's better to connect the Pi's CS so the Pi's SPI peripheral
(hardware) can control the CS signal automatically. The additions are direct
connections from the radio's DIOn pins to the Pi's GPIO and the GPS's Pulse Per
Second (PPS) signal to the Pi.

Below is a table of the connections between the Raspberry Pi and the
LoRa radio.  The "Mod" column indicates where I needed to solder
a wire to make the connection.  If the Mod column is empty that means the
connection is made by a trace in the Dragino PCB.

======   ========   ===   ===   ===   =========   ===
Device   Signal     pin         pin   Pi signal   Mod
======   ========   ===   ===   ===   =========   ===
LoRa     SPI MISO   10          21    SPI0 MISO
LoRa     SPI MOSI   11          19    SPI0 MOSI
LoRa     SPI SCLK   12          23    SPI0 SCLK
LoRa     SPI SS     13          22    GPIO 25     1
LoRa     SPI SS     13          24    SPI0 CS0    W
LoRa     DIO0       6           7     GPIO 4
LoRa     DIO1       7           16    GPIO 23
LoRa     DIO2       8           18    GPIO 24
LoRa     DIO3       3           31    GPIO 6      W
LoRa     DIO4       4           29    GPIO 5      W
LoRa     DIO5       15          15    GPIO 22     W
LoRa     RESET      14          11    GPIO 17
======   ========   ===   ===   ===   =========   ===

======   ========================================
Mod      Explanation
======   ========================================
W        Added a fly wire
1        Either GPIO25 always remains an unusable input, or cut trace to Pi's pin22.
======   ========================================

.. _Raspberry Pi 3 Model B: https://www.raspberrypi.org/products/raspberry-pi-3-model-b/?resellerType=home
.. _`Dragino LoRa/GPS Hat`: http://wiki.dragino.com/index.php?title=Lora/GPS_HAT
.. _`on Tindie`: https://www.tindie.com/products/edwin/raspberry-pi-hat-featuring-gps-and-lorar-technolog/


Reference
---------

Ahsm
    Augmented Hierarchical State Machine.  A statechart capable of nested states
    with entry and exit handlers and having a message queue to serialize incoming events.

This project contains design files and documentation that may be opened with
open source applications.  The following table gives an application that will
open each type of file:

=========== =============== ==============
Extension   Application     Download link
=========== =============== ==============
.qm         `QP Modeler`_   `github`_
=========== =============== ==============

.. _github: https://github.com/QuantumLeaps/qm/releases
.. _QP Modeler: https://www.state-machine.com/qm/

# HeyMac

HeyMac is a TDMA-style Data Link Layer (2) designed for use with
low data rate radio modems such as a LoRa radio module on a Raspberry Pi 3.
HeyMac will build on top of [lora_driver](https://github.com/dwhall/lora_driver)
the Physical Layer (1) LoRa radio driver. 
HeyMac is written in Python3 using the [pq](https://github.com/dwhall/pq) 
hierarchical state machine framework.

The frame structure and frame control fields are distilled from
the IEEE 802.15.4 MAC and slightly altered to allow a 256 Byte payload.

## HeyMac Frame version 1

The HeyMac frame is composed of two general parts, the header and the payload.
The header is every field before the payload.
There is no CRC or message authentication code because either
the physical layer SHOULD have a CRC or
the network layer SHOULD have a message authentication code.

The following diagram shows the HeyMac frame fields and their order.
The topmost field in the digram is transmitted first.

```
        +----+----+----+----+----+----+----+----+
        |  Frame Control (1 octet)              |
        +----+----+----+----+----+----+----+----+
        |  Lencode (0 or 1 octet)               |
        +----+----+----+----+----+----+----+----+
        |  Version and Sequence (0 or 1 octet)  |
        +----+----+----+----+----+----+----+----+
        |  Extended Type (0 or 1 octet)         |
        +----+----+----+----+----+----+----+----+
        |  Destination Address (0,2 or 8 octets)|
        +----+----+----+----+----+----+----+----+
        |  Source Address (0, 2 or 8 octets)    |
        +----+----+----+----+----+----+----+----+
        |  Network ID (0 or 2 octets)           |
        +----+----+----+----+----+----+----+----+
        |  Payload (variable)                   |
        +----+----+----+----+----+----+----+----+
```

The following sections explain each field in detail.


### Frame Control

The Frame Control (Fctl) field is always present and its value defines
the presence, absence, size or type of the other fields in the header.

```
          7   6   5   4   3   2   1   0 (bit)
        +---+---+---+---+---+---+---+---+
        |  Type | L | P |  DAM  |  SAM  |
        +-------+---+---+-------+-------+
```

Legend:

<dl>
  <dt><strong>Type</strong></dt>
  <dd>Frame Type:
    <ul>
    <li>2b00: Minimum frame</li>
    <li>2b01: MAC frame</li>
    <li>2b10: Next Layer Higher (NLH) frame</li>
    <li>2b11: Extended frame type</li>
    </ul>
    If Frame Type is 2b00, then the Version and Sequence field is absent;
    otherwise the Version and Sequence field is present.
    If Frame Type is 2b11, then the Extended Type field is present in the frame;
    otherwise the Extended Type field is absent.
  </dd>
  <dt><strong>L</strong></dt>
  <dd>Frame Lencode:  If 1, the frame's Lencode field is present;
  otherwise the Lencode field is absent.
  </dd>
  <dt><strong>P</strong></dt>
  <dd>Frame Pending:  If 1, the transmitting device has back-to-back frames
  to send to the same recipient and expects the recipient to keep
  its receiver on until the frame pending bit is zero in a subsequent frame.
  <i>Future: In TSCH mode, the frame pending bit is set to one to indicate
  that the recipient should stay on in the next timeslot and on the same channel
  if there is no link scheduled.</i>
  </dd>
  <dt><strong>DAM</strong></dt>
  <dd>Destination Address Mode:
    <ul>
    <li>2b00: the address field is absent.</li>
    <li>2b01: the address field is 64 bits (8 octets).</li>
    <li>2b10: the address field is 16 bits (2 octets).</li>
    <li>2b11: the address field is 16 bits (2 octets)
    and the Network ID field is present.</li>
    </ul>
    If the Address mode is 2b11 then the Network ID field is present;
    otherwise the Network ID field is absent.
  </dd>
  <dt><strong>SAM</strong></dt>
  <dd>Source Address Mode.  This field's bits have the same meaning as DAM,
  but apply to the Source Address field.
  </dd>
</dl>


### Lencode

When the Lencode field is present, it is an 8-bit unsigned number, n,
where `n + 1` is the entire length of the frame in octets,
counted from the Frame Control field to the end of the Payload.
So Lencode ranges 0..255 to represent frame lengths of 1..256.

### Version and Sequence

When the Version and Sequence field is present, it is an 8-bit unsigned value
consisting of two sub-fields.
The Version subfield is an unsigned 4-bit value indicating the HeyMac protocol version.
The Sequence subfield is an unsigned 4-bit sequence number.
The Version subfield occupies the upper 4 bits, while Sequence occupies the lower 4 bits.

### Extended Type

When the Extended Type field is present, it is an 8-bit unsigned value
that encodes the type of contents contained in the Payload field.
Values and their meanings are TBD.

### Destination Address

When the Destination Address field is present, it is a 16- or 64-bit unsigned value
representing the address of the destination for this frame.

### Source Address

When the Source Address field is present, it is a 16- or 64-bit unsigned value
representing the address of the destination for this frame.

### Network ID

When the Network ID field is present, it is a 16-bit unsigned value
representing this network's identity.
TBD: subfields may indicate network type and instance.

### Payload

When the Payload field is present, it is a stream of payload octets.

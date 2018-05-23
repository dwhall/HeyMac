# HeyMac

HeyMac is a Data Link Layer (Layer 2) protocol designed for use with
low data rate, small payload radio modems such as a Semtech LoRa device.
HeyMac is distilled from and incompatible with IEEE 802.15.4.

This implementation of HeyMac:
* builds on top of [lora_driver](https://github.com/dwhall/lora_driver)
  the Physical Layer (Layer 1) LoRa radio driver.
* is written in Python3 using the [pq](https://github.com/dwhall/pq)
  hierarchical state machine framework.

## HeyMac Frame version 1

The HeyMac frame is composed of three general parts: the header,
optional information elements and the payload.

The length of a HeyMac frame MUST be conveyed by the physical layer.

There is no CRC or message authentication code in this layer
because either the physical layer SHOULD have a CRC or
the network layer SHOULD have a message authentication code.

The following diagram shows the order of the HeyMac frame fields.
The topmost field in the diagram is transmitted first.

```
        +----+----+----+----+----+----+----+----+
        |  Frame Control (1 octet)              |
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
        |  Information Elements (variable)      |
        +----+----+----+----+----+----+----+----+
        |  Payload (variable)                   |
        +----+----+----+----+----+----+----+----+
```

The following sections explain each field in detail.


### Frame Control Field

The Frame Control (Fctl) field is always present and its value defines
the presence, absence, size or type of the other fields in the frame.
Furthermore, the Pending flag is an indication of more frames to follow.

```
          7   6   5   4   3   2   1   0 (bit)
        +---+---+---+---+---+---+---+---+
        |  Type | I | N | X | D | S | P |
        +-------+---+---+-------+-------+
        I := IE(s) follow header
        N := Net ID present
        X := eXtended (64 bit) addressing for Src and Dst
        D := Dst addr present
        S := Src addr present
        P := Pending frame
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

  <dt><strong>I</strong></dt>
  <dd>Information Elements:  If 1, a string of IEs follow the header
  (including any optional field of the header).
  </dd>

  <dt><strong>N</strong></dt>
  <dd>Net ID:  If 1, the two-octet Net ID is present in the header.
  </dd>

  <dt><strong>X</strong></dt>
  <dd>eXtended Addressing:  If 1, the the source and/or destination addresses
  are 8 octets (64 bits) in size, if present.
  If 0, the addresses are 2 octets (16 bits) in size, if present.
  </dd>

  <dt><strong>D</strong></dt>
  <dd>Destination Address:  If 1, the Destination Address is present in the header.
  If the Destination Address is not present, the Destination Address may be derived
  from the destination in the NLH.
  If the Destination Address is not present and there is no destination information
  in the NLH, the Destination Address is assumed to be the Root address (0x0000).
  </dd>

  <dt><strong>S</strong></dt>
  <dd>Source Address:  If 1, the Source Address is present in the header.
  If the Source Address is not present, the Source Address may be derived
  from the source in the NLH.
  If the Source Address is not present and there is no source information
  in the NLH, the Source Address is assumed to be the Root address (0x0000).
  </dd>

  <dt><strong>P</strong></dt>
  <dd>Pending Frame:  If 1, the transmitting device has back-to-back frames
  to send to the same recipient and expects the recipient to acknowledge the
  current frame and then continue receiving until the frame pending bit is zero
  in a subsequent frame.
  <i>TBD: In TSCH mode, the frame pending bit is set to one to indicate
  that the recipient should stay on in the next timeslot and on the same channel
  if there is no link scheduled.</i>
  </dd>
</dl>

A Null Frame is a HeyMac frame where the Fctl field is 0 (8b00000000)
and no payload is present.  The Fctl value of 0 indicates a Minimum type frame
with no IEs, no NetID, no addresses and no Pending frames.
A true Null Frame MUST have an empty payload;
its frame length is 1 as reported by the Physical layer.
However, it is also possible that a Minimum frame is created
with Fctl value of 0 and a payload is present.
In this case the Physical layer reports the frame's length
as greater than 1.

### Version and Sequence Field

The VerSeq field is present unless the Fctl Frame Type is Minimum (2b00).
When the VerSeq field is present, it is an 8-bit unsigned value
consisting of two sub-fields.
The Version subfield occupies the upper 4 bits and indicates the HeyMac protocol version.
The Sequence subfield occupies the lower 4 bits and is an unsigned sequence number.

### Extended Type Field

The Extended Type field is present when the Fctl Frame Type is Extended (2b11).
When the Extended Type field is present, it is an 8-bit unsigned value
that encodes the type of contents contained in the Payload field.
Values and their meanings are TBD.

### Destination Address Field

The Destination Address field is present when the Fctl D bit is set (1b1).
When the Destination Address field is present, it is a two or eight octet (16 or 64 bits)
unsigned value representing the address of the destination for this frame.
If the Fctl X bit is set (1b1), the Destination Address field is 8 octets

### Source Address Field

When the Source Address field is present, it is a two or eight octet (16 or 64 bits)
unsigned value representing the address of the source for this frame.

### Network ID Field

When the Network ID field is present, it is a two octet (16 bits) unsigned value
representing this network's identity.
TBD: subfields may indicate network type and instance.

### Payload

When the Payload field is present, it is a stream of payload octets.
The sum of the header, IE and payload octets MUST fit within the Physical layer's payload.

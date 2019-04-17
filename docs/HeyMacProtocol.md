# HeyMac

HeyMac is a flexible frame definition and communication protocol
designed to carry Data Link (Layer 2) and Network (Layer 3) frames
between modest data rate, small payload radio modems such as the Semtech SX127x.
HeyMac is distilled from and incompatible with IEEE 802.15.4.

HeyMac offers 16- and 64-bit addressing, multi-network and multi-hop capabilities.
Extensions for cryptographic authentication and encryption are possible.


This implementation of HeyMac:
* includes a Physical Layer (Layer 1) LoRa radio driver copied
  from the [lora_driver](https://github.com/dwhall/lora_driver) project.
* is written in Python3 using the [farc](https://github.com/dwhall/farc)
  hierarchical state machine framework.

## HeyMac Frame version 1

The HeyMac frame is composed of three general parts: the header,
optional information elements (IEs) and the payload.

The length of a HeyMac frame MUST be conveyed by the physical layer.
So HeyMac uses LoRa's Explicit Header mode.

There is no CRC or message authentication code in this layer
because either the physical layer SHOULD have a CRC or
the network layer SHOULD have a message authentication code.

The following diagram shows the order of the HeyMac frame fields.
The topmost field in the diagram is transmitted first.

```
    +----+----+----+----+----+----+----+----+---+
    |  Frame Control              (1 octet) |   |
    +----+----+----+----+----+----+----+----+   +
    |  Resender Address  (0, 2 or 8 octets) | C |
    +----+----+----+----+----+----+----+----+ l +
    |  Pending, Ver and Sqnc (0 or 1 octet) | e |
    +----+----+----+----+----+----+----+----+ a +---+
    |  Extended Type         (0 or 1 octet) | r |   |
    +----+----+----+----+----+----+----+----+ t +   +
    |  Network ID           (0 or 2 octets) | e |   |
    +----+----+----+----+----+----+----+----+ x + A +
    |  Destination Address (0,2 or 8 octets)| t | u |
    +----+----+----+----+----+----+----+----+   + t +
    |  Hdr Information Elements  (variable) |   | h |
    +----+----+----+----+----+----+----+----+---+ ' +
    |  Bdy Information Elements  (variable) | C | d |
    +----+----+----+----+----+----+----+----+ r +   +
    |  Source Address    (0, 2 or 8 octets) | y |   |
    +----+----+----+----+----+----+----+----+ p +   +
    |  Payload                   (variable) | t |   |
    +----+----+----+----+----+----+----+----+---+---+
    |  Msg Integrity Check  (0 or N octets) |
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
    |  Type | L | R | N | D | I | S |
    +-------+---+---+-------+-------+

    Type := Frame Type (Min, MAC, NET, Extended)
    L := Long addressing
    R := Resender addr present
    N := Net ID present
    D := Dst addr present
    I := IE(s) present
    S := Src addr present
```

Details:

<dl>
  <dt><strong>Type</strong></dt>
  <dd>Frame Type:
    <ul>
    <li>2b00: Minimum frame</li>
    <li>2b01: MAC frame</li>
    <li>2b10: Network (Layer 3) frame</li>
    <li>2b11: Extended frame type</li>
    </ul>
    If Frame Type is 2b00, then the Version and Sequence field
    and the Resender Address field are absent;
    otherwise those fields are present.
    If Frame Type is 2b11, then the Extended Type field is present in the frame;
    otherwise the Extended Type field is absent.
  </dd>

  <dt><strong>L</strong></dt>
  <dd>Long Addressing:  If 1, the resender, destination and/or source address fields
  are 8 octets (64 bits) in size, if present.
  If 0, the addresses are 2 octets (16 bits) in size, if present.
  </dd>

  <dt><strong>R</strong></dt>
  <dd>Resender Address:  If 1, the Resender Address is present in the header.
  The Resender Address is added to or changed within the frame by a node that detects
  that it is responsible for routing the frame.
  The recipient of a frame uses its own address, the frame's Resender Address
  and the frame's Destination Address to determine frame routing.
  </dd>

  <dt><strong>N</strong></dt>
  <dd>Net ID:  If 1, the two-octet Net ID is present in the header.
  </dd>

  <dt><strong>D</strong></dt>
  <dd>Destination Address:  If 1, the Destination Address is present in the header.
  If the Destination Address is not present, the Destination Address may be derived
  from the destination in the NET layer.
  If the Destination Address is not present and there is no destination information
  in the NET layer, the Destination Address is assumed to be the Root address (0x0000).
  </dd>

  <dt><strong>I</strong></dt>
  <dd>Information Elements:  If 1, a string of one or more IEs
  follow the Destination Address.
  </dd>

  <dt><strong>S</strong></dt>
  <dd>Source Address:  If 1, the Source Address is present in the header.
  If the Source Address is not present, the Source Address may be derived
  from the source in the NET layer.
  If the Source Address is not present and there is no source information
  in the NET layer, the Source Address is assumed to be the Root address (0x0000).
  </dd>
</dl>

A Null Frame is a HeyMac frame where the Fctl field is 0 (8b00000000)
and no payload is present.  The Fctl value of 0 indicates a Minimum type frame
with no addresses, no NetID and no IEs.
A true Null Frame MUST have an empty payload;
its frame length is 1 as reported by the Physical layer.
However, it is also possible that a Minimum frame is created
with Fctl value of 0 and a payload is present.
In this case the Physical layer reports the frame's length
as greater than 1.

### Resender Address Field

The Resender Address field is present when the Fctl R bit is set (1b1).
When the Resender Address field is present, it is a two or eight octet (16 or 64 bits)
unsigned value representing the address of the re-sender for this frame.
If the Fctl L bit is set (1b1), the Resender Address field is 8 octets.
The value of the re-sender address is either the source node's address
or the address of an intermediate node that has identified itself
as responsible for routing the frame along the next hop in its journey
to the destination.

### PVS: Pending, Version and Sequence Field

The PVS field is present when the Fctl P bit is set (1b1).
When the PVS field is present, it is an 8-bit unsigned value
consisting of three sub-fields.

The Pending subfield occupies the most-significiant bit and indicates
the transmitting device has back-to-back frames
to send to the same recipient and expects the recipient to acknowledge the
current frame and then continue receiving until the Pending bit is zero
in a subsequent frame.
The Version subfield occupies the next 3 bits and indicates the HeyMac protocol version.
The Sequence subfield occupies the lower 4 bits and is an unsigned sequence number.

### Extended Type Field

The Extended Type field is present when the Fctl Frame Type is Extended (2b11).
When the Extended Type field is present, it is an 8-bit unsigned value
that encodes the type of contents contained in the Payload field.
Values and their meanings are TBD.

### Network ID Field

The Network ID field is present when the Fctl N bit is set (1b1).
When the Network ID field is present, it is a two octet (16 bits) unsigned value
representing this network's identity.
TBD: subfields may indicate network type and instance.

### Destination Address Field

The Destination Address field is present when the Fctl D bit is set (1b1).
When the Destination Address field is present, it is a two or eight octet (16 or 64 bits)
unsigned value representing the address of the destination for this frame.
If the Fctl L bit is set (1b1), the Destination Address field is 8 octets

### HeyMac Information Elements

One or more Information Elements (IEs) are present when the Fctl I bit is set (1b1).
Information Elements provide meta information about the frame
and the data carried within the frame.

There are optionally Header Information Elements and
optionally Body Information Elements
and a way to distinguish the two.
The difference between Header and Body IEs is that
Body IEs are encrypted when the HeyMac frame is enciphered,
but Header IEs are not.
TODO: Add more details.

### Source Address Field

The Source Address field is present when the Fctl S bit is set (1b1).
When the Source Address field is present, it is a two or eight octet (16 or 64 bits)
unsigned value representing the address of the source, or origin, for this frame.


### Payload

When the Payload field is present, it is a stream of payload octets.
The sum of the header, IE, payload and MIC octets MUST fit
within the Physical layer's payload.

## HeyMac Frame Security

HeyMac offers data confidentiality and data authenticity security services.
Encryption and authentication may be applied independently to a HeyMac frame.
However, an intermediate node may disturb an encrypted frame
if it is not also authenticated.
If both encryption and authentication are enabled, encryption is performed first
and authentication is performed afterward.
Authentication is performed starting at the PVS field and continuing to the end of the payload
(which may be encrypted).

The HeyMac frame structure is specifically organized so that (1) encryption and authentication are
performed on contiguous frame octets and (2) a frame that is routed over multiple hops
may have its Resender Address changed by the routing node without disturbing the
encrypted or authenticated data.

### HeyMac Encryption

An entry in the Header Information Elements indicates encryption is enabled
for a frame.  The IE also gives the encryption method details.

When encryption is enabled, the Body IEs, Source Address and Payload fields
are encrypted.

### HeyMac Authentication

An entry in the Header Information Elements indicates authentication is enabled
for a frame.  The IE also gives the authentication method details.

When authentication is enabled, the authentication is calculated over every field
after (not including) the Resender Address.

Performing authentication generates a Message Integrity Code (MIC)
that must be appended to the frame (and fit withing the physical payload).
HeyMac offers a method to append a truncated MIC if there is limited space
remaining in the physical payload.
Statistical assurances are reduced when the MIC is truncated,
but may be partially regained through chaining and succesful authentication of
consecutive frames (not specified by HeyMac).

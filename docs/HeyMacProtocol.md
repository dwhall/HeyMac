# HeyMac

HeyMac is a flexible frame definition and communication protocol
designed to carry Data Link (Layer 2) and Network (Layer 3) frames
between modest data rate, small payload radio modems such as the Semtech SX127x.
HeyMac is distilled from and incompatible with IEEE 802.15.4.

HeyMac offers 16- and 64-bit addressing, multi-network and multi-hop capabilities.
Extensions for cryptographic authentication and encryption are possible.


This implementation of HeyMac:
* includes the Physical Layer (Layer 1) LoRa radio driver submodule
  from the [sx127x_ahsm](https://github.com/dwhall/sx127x_ahsm) project.
* is written in Python3 using the [farc](https://github.com/dwhall/farc)
  hierarchical state machine framework.

## HeyMac Frame

The HeyMac frame is composed of three general parts: the header,
optional information elements (IEs) and the payload.

The length of a HeyMac frame MUST be conveyed by the physical layer.
So HeyMac uses LoRa's Explicit Header mode.

Frame authentication or encryption is optional.

The following diagram shows the order of the HeyMac frame fields.
The topmost field in the diagram is transmitted first.

```
    +----+----+----+----+----+----+----+----+---+---+
    |  Protocol ID                (1 octet) |   |   |
    +----+----+----+----+----+----+----+----+ C +   +
    |  Frame Control              (1 octet) | l | A |
    +----+----+----+----+----+----+----+----+ e + u +
    |  Extended Type         (0 or 1 octet) | a | t |
    +----+----+----+----+----+----+----+----+ r + h +
    |  Network ID           (0 or 2 octets) | t | e |
    +----+----+----+----+----+----+----+----+ e + n +
    |  Destination Address (0, 2, 8 octets) | x | t |
    +----+----+----+----+----+----+----+----+ t + i +
    |  Hdr Information Elements  (variable) |   | c |
    +----+----+----+----+----+----+----+----+---+ a +
    |  Bdy Information Elements  (variable) | C | t |
    +----+----+----+----+----+----+----+----+ r + e +
    |  Source Address    (0, 2 or 8 octets) | y | d |
    +----+----+----+----+----+----+----+----+ p +   +
    |  Payload                   (variable) | t |   |
    +----+----+----+----+----+----+----+----+---+---+
    |  Msg Integrity Check  (0 or N octets) |
    +----+----+----+----+----+----+----+----+
```

The following sections explain each field in detail.


### Protocol ID

The Protocol ID (PID) field is the very first octet in the frame.
It is used to distinguish HeyMac from other frame types.
A few bits of the PID field are set so as to avoid conflicts
with other prominent protocols.
Specifically, ensuring the three most significant bits are set
will avoid trouble with the LoRaWAN MHDR and the 802.15.4-2015 MHR.
LoRaWAN MHDR Type 3b111 is for Proprietary message types and
802.15.4 MHR type 3b111 is for Extended frame types.

The range of values for PID is 0b111xxxxx or (224-255 decimal).
HeyMac choses the value 0xEA (234 decimal) for its PID.

The PID field is new in HeyMac version 2 and was not present
in version 1.  Use of HeyMac version 1 SHALL cease immediately
to avoid miscommunication.

### Frame Control Field

The Frame Control (Fctl) field is always present and its value defines
the presence, absence, size or type of the other fields in the frame.
Furthermore, the Pending flag is an indication of more frames to follow.

```
      7   6   5   4   3   2   1   0 (bit)
    +---+---+---+---+---+---+---+---+
    |  Type | L | P | N | D | I | S |
    +-------+---+---+-------+-------+

    Type := Frame Type (Min, MAC, NET, Extended)
    L := Long addressing
    P := Pending frame follows
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
    <li>2b01: HeyMac Command frame</li>
    <li>2b10: HeyMac + APv6 (Network Layer 3) frame</li>
    <li>2b11: Extended frame</li>
    </ul>
    If Frame Type is Minimum (2b00), then the PVS field is absent;
    otherwise PVS is present.
    If Frame Type is Extended (2b11), then the Extended frame type field is present;
    otherwise it is absent.
  </dd>

  <dt><strong>L</strong></dt>
  <dd>Long Addressing:  If 1, every address field is 8 octets (64 bits)
  in size, if present. This also applies to any address (such as a resender address)
  in an IE, unless explicitly defined by the IE to be a specific size.
  If 0, the addresses are 2 octets (16 bits) in size, if present.
  </dd>

  <dt><strong>P</strong></dt>
  <dd>Pending frame follows: If 1, the transmitting device has back-to-back frames
  to send to the same recipient and expects the recipient to continue
  receiving until the Pending bit is zero in a subsequent frame.
  The primary use of this feature is to send packet fragments in consecutive
  frames.
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
  <dd>Information Elements:  If 1, a sequence of one or more IEs
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

### Extended Type Field

The Extended Type field is present when the Fctl Frame Type is Extended (2b11).
When the Extended Type field is present, it is an 8-bit unsigned value
that encodes the type of contents contained in the remaining frame.
This means that the this frame has unique contents after the the first two octets.
The values and meanings are defined by the specific extension.

Extended Frame structure:

```
    +----+----+----+----+----+----+----+----+
    |  Protocol ID                (1 octet) |
    +----+----+----+----+----+----+----+----+
    |  Frame Control              (1 octet) |
    +----+----+----+----+----+----+----+----+
    |  Extended Type              (1 octet) |
    +----+----+----+----+----+----+----+----+
    |  Extension-specific data   (variable) |
    +----+----+----+----+----+----+----+----+
```

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

Intended use for IEs include:
- a resender address for directed multi-hop routing
- a packet sequence number
- meta-data about the frame authentication algorithm
- meta-data about the frame encryption algorithm

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

### HeyMac Encryption

An entry in the Header Information Elements indicates encryption is enabled
for a frame.  The IE also gives the encryption method details.
When encryption is enabled, the Body IEs, Source Address and Payload fields
are encrypted.  The Header IEs are not encrypted.

### HeyMac Authentication

An entry in the Header Information Elements indicates authentication is enabled
for a frame.  The IE also gives the authentication method details.

When authentication is enabled, the authentication is calculated over every
octet in the frame.
How to handle authentication when a resender modifies the Resender Address IE
is TBD.

Performing authentication generates a Message Integrity Code (MIC)
that must be appended to the frame (and fit within the physical payload).
HeyMac offers a method to append a truncated MIC if there is limited space
remaining in the physical payload.
Statistical assurances are reduced when the MIC is truncated,
but may be partially recovered through chaining and successful authentication
of consecutive frames (not specified by HeyMac).

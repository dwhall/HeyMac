HeyMac
======

HeyMac is a flexible frame definition and communication protocol
designed to carry Data Link (Layer 2) and Network (Layer 3) frames
between small payload radio modems such as the Semtech SX127x.
HeyMac is distilled from and incompatible with IEEE 802.15.4.

HeyMac offers 16- and 64-bit addressing, multi-network and multi-hop capabilities.
Extensions for cryptographic authentication and encryption are possible.


This implementation of HeyMac is written in Python3 using the [farc](https://github.com/dwhall/farc)
  hierarchical state machine framework.


HeyMac Frame
------------

The HeyMac frame is very dynamic.  Only the first two fields, Protocol ID
and Frame Control, are required.  The Frame Control field defines which
of the other fields are present.  The length of a HeyMac frame
MUST be conveyed by the physical layer.
HeyMac uses LoRa's Explicit Header mode to convey the physical frame length.

Frame authentication and encryption are each optional.
If both signing and encryption take place, signing is done first
and then the signature is encrypted.  The following diagram shows the order
of the HeyMac frame fields and which fields are covered by
authentication and which fields are encrypted.
The topmost field in the diagram is transmitted first.

::

    +----+----+----+----+----+----+----+----+---+---+
    |  Protocol ID                (1 octet) | C |   |
    +----+----+----+----+----+----+----+----+ l +   +
    |  Frame Control              (1 octet) | e | A |
    +----+----+----+----+----+----+----+----+ a + u +
    |  Network ID           (0 or 2 octets) | r | t |
    +----+----+----+----+----+----+----+----+ t + h +
    |  Destination Address (0, 2, 8 octets) | e | e |
    +----+----+----+----+----+----+----+----+ x + n +
    |  Hdr Information Elements  (variable) | t | t |
    +----+----+----+----+----+----+----+----+---+ i +
    |  Bdy Information Elements  (variable) |   | c |
    +----+----+----+----+----+----+----+----+ C + a +
    |  Source Address    (0, 2 or 8 octets) | r | t |
    +----+----+----+----+----+----+----+----+ y + e +
    |  Payload                   (variable) | p | d |
    +----+----+----+----+----+----+----+----+ t +   +
    |  Msg Integrity Code   (0 or N octets) |   |   |
    +----+----+----+----+----+----+----+----+---+---+
    |  Hops                  (0 or 1 octet) |
    +----+----+----+----+----+----+----+----+
    |  Transmitter Addr  (0, 2 or 8 octets) |
    +----+----+----+----+----+----+----+----+


The following sections explain each field in detail.


Protocol ID
~~~~~~~~~~~

The Protocol ID (PID) field is the very first octet in the frame.
It is used to distinguish HeyMac frames from other protocols
and to distinguish among the types of HeyMac protocols.
The most significant bits of the PID field are set in order to
avoid conflicts with other prominent protocols.
Specifically, ensuring the three most significant bits are set
will avoid trouble with the LoRaWAN MHDR and the 802.15.4-2015 MHR.
LoRaWAN MHDR Type 3b111 is for Proprietary message types and
802.15.4 MHR type 3b111 is for Extended frame types.

=========== =================================
bit pattern Protocol
=========== =================================
1110 0vvv   HeyMac TDMA, major (vvv)ersion
1110 1vvv   HeyMac CSMA, major (vvv)ersion
1111 xxxx   HeyMac RFU (Flood?, etc.)
=========== =================================

The lower bits of the PID field are used for the protocol version.
However, only the lower two or three of those bits are necessary.
If we ever need to represent more protocols, we can consume
one bit from the (vvv)ersion subfield.


Frame Control Field
~~~~~~~~~~~~~~~~~~~

The Frame Control (Fctl) field is always present and its value defines
the presence, absence, size or type of the other fields in the frame.
Furthermore, the Pending flag is an indication of more frames to follow.

::

      7   6   5   4   3   2   1   0 (bit)
    +---+---+---+---+---+---+---+---+
    | X | L | N | D | I | S | M | P |
    +---+---+---+---+---+---+---+---+

    X := eXtended frame indicator
    L := Long addressing
    N := Net ID present
    D := Dst addr present
    I := IE(s) present
    S := Src addr present
    M := Multihop fields are present
    P := Pending frame to follow

Details:

**X: Extended Frame**
    If the X bit is set, the remaining bits in the Fctl field no longer hold
    the meaning given above.  Instead, the remaining seven bits become the Extended Frame Id.
    Furthermore, the meaning of every octet following the Fctl field is determined by the Extended Frame Id.

**L: Long Addressing**
    If 1, every address field is 8 octets (64 bits)
    in size, if present. This also applies to any address (such as a resender address)
    in an IE, unless explicitly defined by the IE to be a specific size.
    If 0, the addresses are 2 octets (16 bits) in size, if present.

**N: Net ID**
    If 1, the two-octet Net ID is present in the header.

**D: Destination Address**
    If 1, the Destination Address is present in the header.
    If the Destination Address is not present, the Destination Address may be derived
    from the destination in the NET layer.
    If the Destination Address is not present and there is no destination information
    in the NET layer, the Destination Address is assumed to be the Root address (0x0000).

**I: Information Elements**
    If 1, a sequence of one or more IEs
    follow the Destination Address.

**S: Source Address**
    If 1, the Source Address is present in the header.
    If the Source Address is not present, the Source Address may be derived
    from the source in the NET layer.
    If the Source Address is not present and there is no source information
    in the NET layer, the Source Address is assumed to be the Root address (0x0000).

**M: Multihop**
    If 1, the Hops and TxAddr fields are present in the footer.
    The Hops field is one octet that gives the remaining number of hops this frame
    may be retransmitted.  The TxAddr field is the address of the
    node that is retransmitting this frame.

**P: Pending frame follows**
    If 1, the transmitting device has back-to-back frames
    to send to the same recipient and expects the recipient to continue
    receiving until the Pending bit is zero in a subsequent frame.
    The primary use of this feature is to send packet fragments in consecutive
    frames.


Extended Frame Type
~~~~~~~~~~~~~~~~~~~

When the PID field specifies HeyMac and the Fctl's X bit is set (1b1),
the remaining bits in Fctl specify the Extended Frame Id
and the remaining bits in the frame are specific to the Etended Frame type.

Extended Frame structure:

::

      7    6    5    4    3    2    1    0   (bit)
    +----+----+----+----+----+----+----+----+
    |  Protocol ID, Version       (1 octet) |
    +----+----+----+----+----+----+----+----+
    | X  |    Extended Frame Id   (1 octet) |
    +----+----+----+----+----+----+----+----+
    |  Extension-specific data   (variable) |
    +----+----+----+----+----+----+----+----+


Network ID Field
~~~~~~~~~~~~~~~~

The Network ID field is present when the Fctl N bit is set (1b1).
When the Network ID field is present, it is a two octet (16 bits) unsigned value
representing this network's identity.

TBD: the Network ID may indicate network type and instance.


Destination Address Field
~~~~~~~~~~~~~~~~~~~~~~~~~

The Destination Address field is present when the Fctl D bit is set (1b1).
When the Destination Address field is present, it is a two or eight octet (16 or 64 bits)
unsigned value representing the address of the destination for this frame.
If the Fctl L bit is set (1b1), the Destination Address field is 8 octets


Information Elements
~~~~~~~~~~~~~~~~~~~~

One or more Information Elements (IEs) are present when the Fctl I bit is set (1b1).
Information Elements provide meta information about the frame
and the data carried within the frame.

There are optionally Header Information Elements and
optionally Payload Information Elements
and a way to distinguish the two.
The difference between Header and Payload IEs is that
Header IEs are not encrypted when the HeyMac frame is encrypted.

Intended use for IEs include:
- a packet sequence number
- message fragmentation information
- message integrity algorithm info
- message cipher algorithm info

HeyMac Information Elements::

    hIE: header IE: not encrypted, may be authenticated
    pIE: payload IE: may be encrypted and/or authenticated

    IE    := {IEctl [, [length,] extra data]}
    IEctl := [SzTTTTTT] (8b)
    Sz    := Size (2b)
    TTTTT := Type (6b)

=== ==================================================
Sz  meaning
=== ==================================================
00  1b data in lsb of Sz.  No length or extra data.
01  1b data in lsb of Sz.  No length or extra data.
10  No length byte, 2B of extra data.
11  first byte of extra data is length of data that follows
=== ==================================================

hIE := the MSb of TTTTTT is 0
pIE := the MSb of TTTTTT is 1

The IE field is a sequence of IEs.
The hIE MUST come before any pIE.
IFF an hIE exists in the IE field,
the sequence of hIE MUST be terminated by the TERMh IE.
The IE field, if present, MUST be terminated by the TERMp IE.

==========  === ====================================
Sz pTTTTT   h/p IE
==========  === ====================================
00 000000   h   TERMh hIE sequence terminator
10 000001   h   Sequence number
10 000010   h   CIPHER Encipher info
----------  --- ------------------------------------
00 100000   p   TERMp pIE sequence terminator
10 100001   p   FRAG0 First fragment info
10 100010   p   FRAGN Subsequent fragment info
10 100011   p   MIC Message Integrity Code info
==========  === ====================================


Source Address Field
~~~~~~~~~~~~~~~~~~~~

The Source Address field is present when the Fctl S bit is set (1b1).
When the Source Address field is present, it is a two or eight octet (16 or 64 bits)
unsigned value representing the address of the source, or origin, for this frame.


Payload
~~~~~~~

When the Payload field is present, it is a stream of payload octets.
The sum of the header, IE, payload and MIC octets MUST fit
within the Physical layer's payload.


HeyMac Frame Security
---------------------

HeyMac offers data confidentiality and data authenticity security services.
Encryption and authentication may be applied independently to a HeyMac frame.
However, an intermediate node may disturb an encrypted frame
if it is not also authenticated.
If both encryption and authentication are enabled, encryption is performed first
and authentication is performed afterward.
Authentication is performed starting at the PID field
and continuing to the end of the payload (which may be encrypted).
The Message Integrity Code (MIC) is appended immediately after the payload.
The size of the MIC is determined by the IE which specifies the authentication algorithm.

HeyMac Encryption
~~~~~~~~~~~~~~~~~

A Header Information Element indicates encryption is enabled for a frame.
The IE also gives the encryption method details.
When encryption is enabled, the Body IEs, Source Address and Payload fields
are encrypted.  If Authentication is enabled, the MIC is encrypted as well.
The Header IEs are not encrypted.

HeyMac Authentication
~~~~~~~~~~~~~~~~~~~~~

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


Multihop Messages
~~~~~~~~~~~~~~~~~

The Fctl M bit indicates that the frame contains two fields in the frame footer,
Hops and TxAddr.  The Hops field is one octet that gives the remaining number
of hops this frame may be retransmitted.  The TxAddr field is the address of the
node that is retransmitting this frame.

Since a HeyMac frame may be encrypted and sent via a multi-hop route,
the Destination Address is not encrypted and the re-transmitting node
must overwrite the TxAddr with its own address in order for there to be
enough information for multihop routing.

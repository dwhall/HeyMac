HeyMac and APv6 Overview
========================

HeyMac_ and APv6 are complementary technologies intended for use in
low-datarate, lossy, ad-hoc, multi-hop, mobile, wireless networking.
HeyMac is a Layer 2 and 3 frame and protocol definition
that distills ideas and features from `IEEE 802.15.4`_, RPL_ and HiLow_.
APv6 is an IPv6 and UDP adaptation layer that steals from 6LoWPAN_.
APv6 and HeyMac do their best to establish a petite IoT stack
that can be understood and implemented by a dedicated individual.

.. _HeyMac: https://github.com/dwhall/HeyMac
.. _`IEEE 802.15.4`: https://en.wikipedia.org/wiki/IEEE_802.15.4
.. _RPL: https://en.wikipedia.org/wiki/RPL_(IPv6_Routing_Protocol_for_LLNs)
.. _HiLow: https://tools.ietf.org/html/draft-daniel-6lowpan-hilow-hierarchical-routing-01
.. _6LoWPAN: https://en.wikipedia.org/wiki/6LoWPAN


L1: Radio Modem
---------------

APv6 and HeyMac are designed as layered technologies and could
be applied to a number of physical layers.  At this time,
the `Semtech SX127x LoRa`_ family of radio modems are the primary target.
LoRa devices are long-range, low-cost, low-power and multi-band
(433 MHz for licensed US amateurs or 915 Mhz for unlicensed individuals).

- Semtech SX127x using LoRa CSS + FEC
- +14dBm PA, 168dB maximum link budget
- 256B payload
- (BandWidth, SpreadFactor, CodingRate) --> (bitrate, sensitivity)

.. _`Semtech SX127x LoRa`: https://www.semtech.com/products/wireless-rf/lora-transceivers/sx1276


L2: Frame Definition & Identification
-------------------------------------

HeyMac defines a flexible frame format to fit in LoRa's physical payload.
The HeyMac frame provides:

1) a Protocol ID octet to identify the type and subtype of HeyMac frame
2) a Frame Control octet that defines the shape and size of the header and optional footer
3) Network ID, Source and Destination address fields
4) Information Elements for meta-data

A few of the fields may be absent if they are not needed.
The address fields may be absent or short (2 octets) or long (8 octets).

A specially-formed `Identification Certificate`_ is the one piece of information
needed to provision a HeyMac node.  An `asymmetric keypair`_ is generated
such that computing a specified hash of the public key
results in the node's statistically-unique, long address.
Linking a public key and an address in this way is called `cryptographic addressing`_.
Note that cryptographic addressing is distinct from message encryption.
However, since every node is provisioned with a unique cryptographic keypair,
message encryption and authentication become available.
Now that a node is provisioned and has its long address, it may begin radio operations.

.. _`Identification Certificate`: https://en.wikipedia.org/wiki/X.509
.. _`asymmetric keypair`: https://en.wikipedia.org/wiki/Public-key_cryptography
.. _`cryptographic addressing`: https://en.wikipedia.org/wiki/Cryptographically_Generated_Address


L2: Neighbors and Links
-----------------------

A beacon is a message that identifies the node with its long address and
provides other pieces of information useful to communication and networking.
By listening to the radio over time and hearing beacons and other messages,
a node builds a list of its immediate neighbors.
Two-way communication with each neighbor is likely, but not guaranteed.
The conditions may be such that a neighbor cannot hear you for some reason.

A node communicates with its neighors by sending broadcast or addressed HeyMac Commands.
There are a handful of HeyMac Commands that do a number of useful things.
The most useful command set is the one used to join a network.


L3: Network Topology
--------------------

In order to reduce the chaos of an ad-hoc network, HeyMac nodes self-organize
into a downward tree topology: the root is at the top and has no parent.
Every non-root node has one parent (up) and zero to fourteen [*]_ children (down).
As nodes come and go, the tree structure is dynamically built and rebuilt
which makes HeyMac networks imperfect, but adaptive and self-healing.
Joining the network is a surprisingly simple process.

Using neighbor beacon data and link quality information, a node picks a networked neighbor
to be its parent and initiates the multi-message HeyMac Join process.
Three messages are sent between the initiator and the parent (2 up, 1 down).
If joining is successful, the parent sends a message to the network root
with the new node's long and short address.  The root tracks such information in order
to provide helpful services such as address lookup and border routing.

It is the parent, not the root, that gives permission for a node to join the network.
This greatly reduces the number of messages used to join a network (compared to 802.15.4)
especially for deeply ranked networks.  It also allows a node to reject having children.
This prevents a transitory node from forming doomed links.


..  [*] fourteen because HeyMac uses a 4-bit radix as a tradeoff
    between the maximum number of hops and maximum number of children.
    4-bits allows sixteen combinations; minus the value zero for self
    and the value fifteen for child-broadcast.


L3: Short Addresses and Routing
-------------------------------

We saw above how a public key resolves into a node's long address.
But that's not the only address a node can have.  When a node joins a network
it is given a shorter address (two octets) to use within that network.
The short address is special because not only is it unique within the network,
but it also denotes the node's position in the network.

HeyMac uses an addressing system called Hierarchically Ordered Numbers
for Routing, 16-bit (HONR16).  This system enables every node to manage the address space
of its children without need to consult the root, a directory service or any other
single point of (failure / consolidated power).  HONR16 addressing also gives
the network a remarkably easy way to route messages.

With all the nodes self-organized into a downward tree and the HONR16 numbering
system reflecting the structure of the tree, it becomes trivial to
determine a route between any two addresses in the network.
For any two nodes, there is a common ancestor between them.
So a message simply has to travel up the tree to the nearest common ancestor
and then down the tree to the destination.
Furthermore, since the message itself contains the destination address,
any node receiving a message can forward the mesage without knowing
the source address.  Thus, HeyMac offers a little bit of anonymity
by allowing the source address of message to be encrypted if so desired.

An up/down route is not an optimal route, but it is reasonably close
and, moreover, is guaranteed to exist as long as both endpoints remain linked to the root.
The simplicity of up/down routing means that keeping a routing table is not necessary.
Even the lowest-memory nodes can perform the essential routing function.
Whereas 802.15.4 networks have reduced function devices (RFDs) that do not route,
the design of HeyMac lets every node be a helpful member.

Sometimes though, a node disappears without warning, a branch breaks from the tree
and the fallen nodes must recover.


L3: Network Maintenance
-----------------------

HeyMac is designed to accomodate nodes that come and go frequently.
Such transient nodes can indicate in their beacon that they should not be targets
for the joining process since they are likely to leave soon.
HeyMac nodes are also given the autonomy to reject join requests at their discretion.
So dependencies won't be built where they are unlikely to thrive.

The HeyMac beacon message includes a flag that indicates the node is unfit to be a parent
(so a node shouldn't attempt to join to it).  That said, there are also times when
a node stops functioning, moves or otherwise leaves the network without warning.
HeyMac provides a way to recover from this situation.  The remaining nodes discover
and indicate the lack of connection to the root and forget that network affiliation.
Then, each dropped node proceeds with the regular joining process.

The rejoining process means two things: (1) a single node might have different
short addresses at different points in time (one fresh, one stale) and
(2) a message that is in-flight during a branch restructuring might contain a stale address.
This address freshness problem is solved by building a sequence number into the tree's Network ID.
Any time the tree's structure changes in such a way to cause stale addresses (routing problems), the root
increments the Network ID's sequence number and broadcasts the new Network ID to all nodes.

While not required, it would be possible for every in-flight message with a stale network ID
to be forwarded to the root.  The root would be capable of translating the stale address
to the fresh address and forwarding the message.


L+: IPv6, UDP and Fragmentation
-------------------------------

HeyMac is designed to work with IPv6 networks by using the APv6 adaptation layer.
APv6 offers both IPv6 and UDP header compression.  Compression benefits the most
when the UDP message travels strictly within the HeyMac network because short addresses
can be used.  However, APv6 also allows 128-bit addressing for bridging and border-routing
to a full-scale IPv6 network.  Unfortunately, TCP traffic will not yet flow into the HeyMac network.

Any carrier of IPv6 must accept packets of up to 1280 octets.  Since this won't fit into
the meager constraint of the LoRa frame (256 octets), APv6 employs the
`Gomez fragmentation header`_ to assist with packet fragmentation and reassembly.

.. _`Gomez fragmentation header`: https://tools.ietf.org/html/draft-gomez-6lo-optimized-fragmentation-header-00


Conclusion
----------

HeyMac and APv6 is designed by an amateur for amateurs using proven research and ideas.
HeyMac offers a small and flexible frame structure for Layer 2 and 3 communications
while APv6 offers a byte-efficient adaptation layer for IPv6 UDP traffic.
Together, these two technologies allow the automatic construction of an ad-hoc wireless
network with a simple and deterministic routing algorithm.
Using HeyMac and APv6 on Semtech LoRa modems results in a multi-hop radio data network
that offers great link distances for such little radiated power in sub-GHz ISM and
US amateur radio bands.

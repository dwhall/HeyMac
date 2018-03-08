# A time slot (tslot) is a window of time to complete a 256 byte frame
# and an acknowledgement frame.  The HeyMac protocol uses a whole number
# of tslots within one second.
tslots_per_sec = 4

# A whole number of consecutive tlots form a superframe (sframe).
# There must be enough tslots so that every node in a two-hop range
# can own at least one tslots in the sframe.
# Values that are multiples of 32 or powers of 2 are convenient and efficient.
tslots_per_sframe = 256

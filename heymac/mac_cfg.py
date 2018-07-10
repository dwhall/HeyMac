# A time slot (tslot) is a window of time to complete a 256 byte frame
# and an acknowledgement frame.  The HeyMac protocol uses a whole number
# of tslots within one second.
TSLOTS_PER_SEC = 4

# A whole number of consecutive tlots form a superframe (Sframe).
# There must be enough tslots so that every node in a two-hop range
# can own at least one tslots in the Sframe.
# Values that are multiples of 32 or powers of 2 are convenient and efficient.
TSLOTS_PER_SFRAME = 128

# The amount of time before the start of a Tslot to activate the software
# so it can decide what to do and perform any preparation so the radio action
# happens as close to the start of a Tslot as possible.
# The following value was determined through experimentation.
# It should be great enough to prevent a busy system from missing the time
# and small enough to not block for a significant amount of time.
TSLOT_PREP_TIME = 0.020 # secs

# The amount of time [seconds] since the reception of a PPS signal
# after which the timing is no longer disciplined.
# The following value is a guess and can be improved.
DSCPLN_PPS_TIMEOUT = 5.0 * 60.0 # five minutes

# The amount of time [seconds] since the reception of a HeyMac beacon
# after which the timing is no longer disciplined.
# This value SHOULD be greater than DSCPLN_PPS_TIMEOUT to allow the weaker
# form of discipline more time to operate.
DSCPLN_BCN_TIMEOUT = 10.0 * 60.0 # ten minutes

# The amount of time between the true start of a Beacon frame
# and the point when the receiver detects reception via DIO3/ValidHeader.
# This time must be accounted for by Beacon discipline.
# This time was determined by comparing 1 receiver's log file:
#   2018-04-25 23:13:42,998 pps            898898.480569
#   2018-04-25 23:13:43,394 rx_time        898898.748040    RXD 139 bytes...
TIME_TO_VALID_HEADER = 0.0175

# The number of Sframes a node should remain in the Listening state
# before transitioning to a state which allows transmitting.
# A decent value is 2.  A smaller value is used for debugging.
N_SFRAMES_TO_LISTEN = 0.5

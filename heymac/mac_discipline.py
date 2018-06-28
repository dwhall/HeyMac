import logging

import mac_cfg


class HeyMacDiscipline:
    """A class to track HeyMac timing discipline
    via GPS Pulse-per-Second (PPS) and RF Beacon arrivals.

    In this context, "timing discipline" is the principle that every node
    must work toward a common, isochronous concept of time so that the nodes are
    able to agree on the boundaries of timeslots which organize when nodes
    transmit, receive or rest.

    PPS is considered the most highly trusted source of timing in HeyMac
    because of its high accuracy and wide availability.  A PPS signal can 
    potentially be heard by every node; whereas an RF Beacon from a single 
    source can only be heard by nodes within range of the source.

    When a PPS is not available, a node should attempt RF Beacon discipline
    by listening for beacons from neighbors who are PPS disciplined.
    Beacons from neighbors who are not PPS disciplined should be used only
    as the last choice.
    """

    def __init__(self,):
        # PPS discipline
        # Error of computer clock time [secs]
        # calculated as: time_at_pps - prev_time_at_pps
        self.pps_err = 0.0
        # Time of the last received GPS PPS
        self.time_of_last_pps = None
        # Count of received PPS edges without a loss of disciplien in between
        self.consec_pps_cnt = 0

        # BCN discipline
        # Error of computer clock time [secs]
        # calculated as: time_at_bcn - prev_time_at_bcn
        self.bcn_err = 0.0
        # Time of the last received BCN
        self.time_of_last_rxd_bcn = None
        # Count of received beacons without a loss of disciplien in between
        self.consec_bcn_cnt = 0

        # Discipline state describes the source of timing discipline
        self._dscpln_st = "none"


    def get_dscpln_as_int(self,):
        """Returns the current state of timing discpline
        as an integer where:
            "none" --> 0
            "bcn"  --> 1
            "pps"  --> 2
        """
        dscpln_int = {
            "none": 0,
            "bcn": 1,
            "pps": 2
        }
        return dscpln_int[self._dscpln_st]


    def get_time_of_next_tslot(self, time_now):
        """Returns the corrected time [float secs] for the next Tslot 
        according to the best discipline source.
        If this node is out of discipline fall back to using the time
        of a discipline mode that had been reached in the past.
        If none of that is available, use this node's CPU time as the discipline
        source.  This will be a somewhat arbitrary timing edge.

        REMINDER: time_now is approx TSLOT_PREP_TIME before the active Tslot.
        So, if we want to calc the _next_ Tslot, we need to think 2 edges ahead.
        """
        if self.time_of_last_pps:
            assert time_now > self.time_of_last_pps
        if self.time_of_last_rxd_bcn:
            assert time_now > self.time_of_last_rxd_bcn

        # PPS discipline
        if self.time_of_last_pps and time_now - self.time_of_last_pps < mac_cfg.DSCPLN_PPS_TIMEOUT:
            self._dscpln_st = "pps"
            tslots_since_last_pps = round((time_now - self.time_of_last_pps) * mac_cfg.TSLOTS_PER_SEC)
            cpu_time_per_tslot = (1.0 - self.pps_err) / mac_cfg.TSLOTS_PER_SEC
            tm = self.time_of_last_pps + (1 + tslots_since_last_pps) * cpu_time_per_tslot

        # BCN discipline
        elif self.time_of_last_rxd_bcn and time_now - self.time_of_last_rxd_bcn < mac_cfg.DSCPLN_BCN_TIMEOUT:
            self._dscpln_st = "bcn"
            tslots_since_last_bcn = round((time_now - self.time_of_last_rxd_bcn) * mac_cfg.TSLOTS_PER_SEC)
            cpu_time_per_tslot = (1.0 - self.bcn_err) / mac_cfg.TSLOTS_PER_SEC
            tm = self.time_of_last_rxd_bcn + (1 + tslots_since_last_bcn) * cpu_time_per_tslot

        # no discipline
        else:
            self._dscpln_st = "none"

            # if never achieved discipline, use this node's CPU time as the source.
            if not self.time_of_last_pps and not self.time_of_last_pps:
                tslot_period = (1.0 / mac_cfg.TSLOTS_PER_SEC)
                remainder = time_now % tslot_period
                time_of_prev_tslot = time_now - remainder
                tm = time_of_prev_tslot + 2 * tslot_period

            # If PPS discipline was achieved and is more recent, use its time
            elif((self.time_of_last_pps and self.time_of_last_rxd_bcn and self.time_of_self.time_of_last_pps > self.time_of_last_rxd_bcn)
                or not self.time_of_last_rxd_bcn):
                tslots_since_last_pps = round((time_now - self.time_of_last_pps) * mac_cfg.TSLOTS_PER_SEC)
                cpu_time_per_tslot = (1.0 - self.pps_err) / mac_cfg.TSLOTS_PER_SEC
                tm = self.time_of_last_pps + (1 + tslots_since_last_pps) * cpu_time_per_tslot

            # otherwise, if beacon discipline was ever achieved and is more recent, use its time
            else:
                tslots_since_last_bcn = round((time_now - self.time_of_last_rxd_bcn) * mac_cfg.TSLOTS_PER_SEC)
                cpu_time_per_tslot = (1.0 - self.bcn_err) / mac_cfg.TSLOTS_PER_SEC
                tm = self.time_of_last_rxd_bcn + (1 + tslots_since_last_bcn) * cpu_time_per_tslot


        # If the next tslot time is too soon to do anything, get the next one.
        # This should only happen when transitioning between HeyMac's Listening
        # and Scheduling states or when transitioning between undisciplined
        # and disciplined timing.
        #
        # WARNING: This MAY result in a miscalculation of ASN in mac_tdma_ahsm
        # and ruin everything.
        #if tm < time_now + mac_cfg.TSLOT_PREP_TIME:
        #    tm += (1.0 / mac_cfg.TSLOTS_PER_SEC)

        assert tm > time_now
        return tm


    def update_bcn(self, time_of_rxd_bcn):
        """Measures the amount of computer clock time that has elapsed
        between this and the previous beacon which should be a multiple of the
        duration of a timeslot.  Calculates the error between the measured and
        the ideal times and keeps an average error, .bcn_err
        """
        # The DIO3/ValidHeader signal used to capture the RX time arrives some
        # amount of time after the beginning of the Beacon frame.  We must
        # remove that time in order to get a good estimate of the Beacon arrival
        time_of_rxd_bcn -= mac_cfg.TIME_TO_VALID_HEADER
        logging.info("adj rxd_bcn    %f" % (time_of_rxd_bcn))


        # Must have received at least one previous bcn in order to measure delta
        if self.time_of_last_rxd_bcn:
            delta = time_of_rxd_bcn - self.time_of_last_rxd_bcn

            # Reset or increment the consecutive beacon count
            if delta > mac_cfg.DSCPLN_BCN_TIMEOUT:
                self.consec_bcn_cnt = 1
            else:
                self.consec_bcn_cnt += 1

                # Remove the whole number of tslots and divide by the number 
                # of slots to get the amount of error per slot
                # in order to maximize significant digits of floating point
                delta *= mac_cfg.TSLOTS_PER_SEC
                whole_slots = float(round(delta))
                err = (delta - whole_slots) / whole_slots
                # Then restore the error to cpu-counts per second
                err /= mac_cfg.TSLOTS_PER_SEC

                # TODO: improve this cheap IIR LP filter
                self.bcn_err = (self.bcn_err + err) * 0.5

        self.time_of_last_rxd_bcn = time_of_rxd_bcn


    def update_pps(self, time_of_pps):
        """Measures the amount of computer clock time that has elapsed
        between this and the previous PPS which should be an whole number
        of seconds.  Calculates the error between the measured and the ideal
        times and keeps an average error, .pps_err
        """
        # Must have received at least one previous PPS in order to measure delta
        if self.time_of_last_pps:
            delta = time_of_pps - self.time_of_last_pps

            # Reset or increment the consecutive PPS count
            if delta > mac_cfg.DSCPLN_PPS_TIMEOUT:
                self.consec_pps_cnt = 1
            else:
                self.consec_pps_cnt += 1

                # Remove the whole seconds and divide by the number of secs
                # to get the amount of error per second 
                # in order to maximize significant digits of floating point
                whole_secs = float(round(delta))
                err = (delta - whole_secs) / whole_secs

                # TODO: improve this cheap IIR LP filter
                self.pps_err = (self.pps_err + err) * 0.5

        self.time_of_last_pps = time_of_pps

import mac_cfg


class HeyMacDiscipline:
    """A class to track HeyMac timing discipline
    via GPS PPS and RF Beacon arrivals.
    """
    def __init__(self,):
        # Error of computer clock time [secs]
        # calculated as: time_at_pps - prev_time_at_pps
        self.pps_err = 0.0
        # Time of the previous GPS PPS
        self.time_of_last_pps = None

        # Error of computer clock time [secs]
        # calculated as: time_at_bcn - prev_time_at_bcn
        self.bcn_err = 0.0
        # Time of the previous BCN
        self.time_of_last_rxd_bcn = None


    def update_pps(self, time_of_pps, time_of_last_pps):
        """This function is called every time the PPS pulses.
        This function saves the PPS time and calculates the error of the
        system clock compared to the PPS reference.
        """
        # If there are two PPS pulses within the following amount of time [secs],
        # then use the delta between PPS pulses to calculate the
        # computer clock time per second.
        PPS_GAP_TOLERANCE = 10.0 # this value is a guess

        if time_of_last_pps:
            delta = time_of_pps - time_of_last_pps
            if delta < PPS_GAP_TOLERANCE:

                # Remove the whole seconds and divide by the number of secs
                # to get the amount of error per second 
                # (and maximize significant digits)
                whole_secs = round(delta)
                err = (delta - whole_secs) / whole_secs

                # TODO: improve this cheap IIR LP filter
                self.pps_err = (self.pps_err + err) * 0.5


    def update_bcn(self, time_of_rxd_bcn, time_of_last_rxd_bcn):
        """Measures the amount of computer clock time that has elapsed
        since the previous received beacon.  Calculates the amount of error
        between the two and generates an average error, .bcn_err
        """
        # If there are two beacons within the following amount of time [secs],
        # then use the delta between beacons to calculate the
        # computer clock time per second.
        # (assumes beacons happen at top-of-second (same as PPS))
        BCN_GAP_TOLERANCE = 4 *  mac_cfg.TSLOTS_PER_SFRAME

        if time_of_last_rxd_bcn:
            delta = time_of_rxd_bcn - time_of_last_rxd_bcn
            if delta < BCN_GAP_TOLERANCE:

                # Remove the whole seconds and divide by the number of secs
                # to get the amount of error per second
                whole_secs = round(delta)
                err = (delta - whole_secs) / whole_secs

                # TODO: improve this cheap IIR LP filter
                self.bcn_err = (self.bcn_err + err) * 0.5


    def get_time_per_tslot(self,):
        """Returns the corrected time [float secs] for 1 Tslot according to the best source.
        """
        #TODO: determine best source
        return (1.0 - self.pps_err) / mac_cfg.TSLOTS_PER_SEC
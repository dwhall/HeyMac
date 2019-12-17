"""
Copyright 2018 Dean Hall.  See LICENSE file for details.

HeyMac Frame structure definition
and methods to get/set frame fields.

This file requires the excellent third-party module 'dpkt'
which may be installed via::

    pip install dpkt
"""


import logging

import dpkt # pip install dpkt

from .mac_cmds import *
from .net_frame import APv6Frame


class HeyMacFrame(dpkt.Packet):
    """HeyMac frame definition
    [PID,Fctl,NetId,DstAddr,IEs,SrcAddr,Payld,MIC,Hops,TxAddr]
    """
    # HeyMac Protocol ID
    # XXX. ....     Protocol
    # ...X X...            Type
    # .... .XXX                  Version
    # 1110 0vvv     HeyMac TDMA, (vvv)ersion
    # 1110 1vvv     HeyMac CSMA, (vvv)ersion
    # 1111 xxxx     HeyMac (RFU: Flood, Extended, etc.)
    # PID field masks
    PID_PROTOCOL_MASK = 0b11100000
    PID_TYPE_MASK = 0b00011000
    PID_VER_MASK = 0b00000111
    # PID field values
    PID_PROTOCOL_HEYMAC = 0b11100000
    PID_TYPE_TDMA = 0b00000000
    PID_TYPE_CSMA = 0b00001000
    PID_VER_TDMA = 0b00000000
    PID_VER_CSMA = 0b00000000

    SUPPORTED_CSMA_VERS = (0,)
    SUPPORTED_TDMA_VERS = (0,)

    PID_HEYMAC_CSMA_0 = PID_PROTOCOL_MASK | PID_TYPE_CSMA | 0

    # Frame Control Field (Fctl) subfield values
    FCTL_X_SHIFT = 7 # Extended frame (none of the other bits apply)
    FCTL_L_SHIFT = 6 # Long addressing
    FCTL_N_SHIFT = 5 # NetId present
    FCTL_D_SHIFT = 4 # DstAddr present
    FCTL_I_SHIFT = 3 # IEs present
    FCTL_S_SHIFT = 2 # SrcAddr present
    FCTL_M_SHIFT = 1 # Multihop fields present
    FCTL_P_SHIFT = 0 # Pending frame follows

    __byte_order__ = '!'  # Network order
    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties .pid_protocol, .fctl, .fctl_l, .fctl_n, etc. instead.
        ('_pid', 'B', PID_HEYMAC_CSMA_0),
        ('_fctl', 'B', 0),
        # The fields above are guaranteed to be present.
        # Below this are optional fields.
        # The type spec '0s' lets us consume a variable number of bytes
        # for the field.
        ('netid', '0s', b''),
        ('daddr', '0s', b''),
        ('hie', '0s', b''), # header IEs appear in cleartext
        ('bie', '0s', b''), # body IEs may be enciphered
        ('saddr', '0s', b''),
#        ('_', '0s', b''), # use .data to access payload
        ('mic', '0s', b''),
        ('hops', '0s', b''),
        ('txaddr', '0s', b''),
    )

    # Functions to help determine which fields are present
    def _is_extended_frame(self,):
        return self.fctl_x != 0
    def _has_netid_field(self,):
        return self.fctl_n != 0
    def _has_daddr_field(self,):
        return self.fctl_d != 0
    def _has_ie_field(self,):
        return self.fctl_i != 0
    def _has_saddr_field(self,):
        return self.fctl_s != 0
    def _has_multihop_fields(self,):
        return self.fctl_m != 0

    # Functions to determine size of variable-size fields
    def _sizeof_addr_field(self,):
        """Assumes caller has determined the addr field is present
        """
        if self.fctl_l != 0:
            sz = 8
        else:
            sz = 2
        return sz

    def _sizeof_ie_fields(self,):
        """Returns the sizes of the hIE and bIE fields
        as a tuple (size_of_hIE, size_of_bIE).
        These sizes are variable from one packet to another
        but are fixed for a given packet and are calculated by
        parsing the contents of the hIE and bIE fields.
        """
        # FIXME
        return (0,0)


    # Getters for the _pid field
    @property
    def pid(self,):
        return self._pid

    @property
    def pid_protocol(self,):
        """Gets the Protocol value in the PID field.
        """
        return self._pid & HeyMacFrame.PID_PROTOCOL_MASK

    @property
    def pid_type(self,):
        """Gets the Type value in the PID field.
        """
        return self._pid & HeyMacFrame.PID_TYPE_MASK

    @property
    def pid_ver(self,):
        """Gets the Version value in the PID field.
        Returns None if the type is not TDMA or CSMA.
        """
        ver = None
        if self.pid_type in (HeyMacFrame.PID_TYPE_TDMA, HeyMacFrame.PID_TYPE_CSMA):
            ver = self._pid & HeyMacFrame.PID_VER_MASK
        return ver

    # Setters for the _pid field
    @pid_protocol.setter
    def pid_protocol(self, val):
        """Sets the Protocol value in the PID field.
        """
        self._pid &= ~HeyMacFrame.PID_PROTOCOL_MASK
        self._pid |= (val & HeyMacFrame.PID_PROTOCOL_MASK)

    @pid_type.setter
    def pid_type(self, val):
        """Sets the Type value in the PID field.
        """
        self._pid &= ~HeyMacFrame.PID_TYPE_MASK
        self._pid |= (val & HeyMacFrame.PID_TYPE_MASK)

    @pid_ver.setter
    def pid_ver(self, val):
        """Sets the Version value in the PID field.
        """
        self._pid &= ~HeyMacFrame.PID_VER_MASK
        self._pid |= (val & HeyMacFrame.PID_VER_MASK)

    # Getters for the _fctl field
    @property
    def fctl(self,):
        """Gets the full value (all bits) from the Fctl field.
        """
        return self._fctl

    @property
    def fctl_x(self,):
        """Gets the Extended frame flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_X_SHIFT)

    @property
    def fctl_l(self,):
        """Gets the Long address flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_L_SHIFT)

    @property
    def fctl_p(self,):
        """Gets the Pending frames flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_P_SHIFT)

    @property
    def fctl_n(self,):
        """Gets the NetID present flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_N_SHIFT)

    @property
    def fctl_d(self,):
        """Gets the Dest address present flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_D_SHIFT)

    @property
    def fctl_i(self,):
        """Gets the IE present flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_I_SHIFT)

    @property
    def fctl_s(self,):
        """Gets the Src address present flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_S_SHIFT)

    @property
    def fctl_m(self,):
        """Gets the Multihop flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_M_SHIFT)


    # Setters for the _fctl field
    @fctl.setter
    def fctl(self, val):
        """Sets the full value (all bits) in the Fctl field.
        """
        self._fctl = val

    def _fctl_setter_for_bit(self, val, bit_idx):
        """Sets or clears one of the X,L,N,D,I,S,M,P bits
        without modifying the Type bits.
        """
        assert 0 <= val <= 1
        assert 0 <= bit_idx <= 7
        self._fctl &=  ~(1 << bit_idx)
        self._fctl |= (val << bit_idx)

    @fctl_x.setter
    def fctl_x(self, val):
        """Sets the Extended value in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_X_SHIFT)

    @fctl_l.setter
    def fctl_l(self, val):
        """Sets the Long address flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_L_SHIFT)

    @fctl_p.setter
    def fctl_p(self, val):
        """Sets the Pending frames flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_P_SHIFT)

    @fctl_n.setter
    def fctl_n(self, val):
        """Sets the NetID present flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_N_SHIFT)

    @fctl_d.setter
    def fctl_d(self, val):
        """Sets the Dest address present flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_D_SHIFT)

    @fctl_i.setter
    def fctl_i(self, val):
        """Sets the IEs present flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_I_SHIFT)

    @fctl_s.setter
    def fctl_s(self, val):
        """Sets the Source address present flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_S_SHIFT)

    @fctl_m.setter
    def fctl_m(self, val):
        """Sets the Multihop flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_M_SHIFT)


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        super().unpack(buf)

        # validate the PID
        if not self.is_heymac():
            raise ValueError("Invalid PID value")

        # The Fctl field can be every bit-combination
        # so there's no illegal value; no way to validate.
        # All fields after Fctl are optional (defined as '0s')
        # so we conditionally pull them from the .data bytearray

        if self._has_netid_field():
            if len(self.data) < 2:
                raise dpkt.NeedData("for netid")
            self.netid = self.data[0:2]
            self.data = self.data[2:]

        if self._has_daddr_field():
            sz = self._sizeof_addr_field()
            if len(self.data) < sz:
                raise dpkt.NeedData("for daddr")
            self.daddr = self.data[0:sz]
            self.data = self.data[sz:]

        if self._has_ie_field():
            sz_hie, sz_bie = self._sizeof_ie_fields()
            if len(self.data) < sz_hie + sz_bie:
                raise dpkt.NeedData("for IEs")
            self.hie = self.data[0:sz_hie]
            self.bie = self.data[sz_hie:sz_hie + sz_bie]
            self.data = self.data[sz_hie + sz_bie:]

        if self._has_saddr_field():
            sz = self._sizeof_addr_field()
            if len(self.data) < sz:
                raise dpkt.NeedData("for saddr")
            self.saddr = self.data[0:sz]
            self.data = self.data[sz:]

        # The payload comes after SrcAddr, but its size is unknown.
        # So we parse any multihop data from the tail of the packet, backward.
        if self._has_multihop_fields():
            sz = 1 + self._sizeof_addr_field()
            if len(self.data) < sz:
                raise dpkt.NeedData("for hops/txaddr")
            self.txaddr = self.data[-sz:]
            self.data = self.data[:-sz]
            self.hops = self.data[-1:]
            self.data = self.data[:-1]

        # At this point self.data contains the payload, which may be empty.
        # The first byte of the payload denotes its type.
        # Create an instance of its type and keep it as self.payld
        if self.data:
            if self.is_data_net_layer(self.data[0]):
                try:
                    self.payld = APv6Frame(self.data)
                except:
                    logging.info("invalid APv6 frame: %b", self.data)
            elif self.is_data_mac_layer(self.data[0]):
                try:
                    self.payld = HeyMacCmdInstance(self.data)
                except:
                    logging.info("invalid MAC cmd %d", self.data[0] & HeyMacCmd.CMD_MASK)


    def pack_hdr(self):
        """Packs header attributes into a bytes object.
        This function is called when bytes() or len() is called
        on an instance of HeyMacFrame.
        """
        d = bytearray()

        # Skip PID and Fctl fields for now,
        # insert them at the end of this function

        if self.netid:
            self.fctl_n = 1
            if type(self.netid) is int:
                self.netid = struct.pack("!H", self.netid)
            assert len(self.netid) == 2
            d.extend(self.netid)

        if self.daddr:
            if type(self.daddr) is int:
                self.daddr = struct.pack("!H", self.daddr)
            len_daddr = len(self.daddr)
            if len_daddr == 8:
                self.fctl_l = 1
                self.fctl_d = 1
            elif len_daddr == 2:
                self.fctl_d = 1
            d.extend(self.daddr)

        # TODO: add IEs

        if self.saddr:
            if type(self.saddr) is int:
                self.saddr = struct.pack("!H", self.saddr)
            len_saddr = len(self.saddr)
            if len_saddr == 8:
                self.fctl_l = 1
                self.fctl_s = 1
            elif len_saddr == 2:
                self.fctl_s = 1
            d.extend(self.saddr)

# FIXME: this combined with super().pack_hdr() below causes two copies of payload.
#        if self.data:
#            d.extend(self.data)

        if self.hops:
            assert bool(self.txaddr)
            if type(hops) is int:
                self.hops = struct.pack("B", self.hops)
            d.append(self.hops)

        if self.txaddr:
            assert bool(self.hops)
            if type(self.txaddr) is int:
                self.txaddr = struct.pack("!H", self.txaddr)
            len_txaddr = len(self.txaddr)
            if len_txaddr == 8:
                self.fctl_l = 1
                self.fctl_m = 1
            elif len_txaddr == 2:
                self.fctl_m = 1
            d.extend(self.txaddr)

        # Inserts PID and Fctl,
        # returns the combined bytes object
        return super().pack_hdr() + bytes(d)


    # API
    def is_heymac(self, pid_type=PID_TYPE_CSMA):
        """Returns TRUE if the frame header PID Protocol field is HeyMac
        and the PID Type field matches the given argument.
        Does not check the PID Version field.
        """
        return (self.pid_protocol == HeyMacFrame.PID_PROTOCOL_HEYMAC
            and self.pid_type == pid_type)

    def is_heymac_version_compatible(self,):
        if self.pid_type == HeyMacFrame.PID_TYPE_CSMA:
            return self.pid_ver in HeyMacFrame.SUPPORTED_CSMA_VERS
        elif self.pid_type == HeyMacFrame.PID_TYPE_TDMA:
            return self.pid_ver in HeyMacFrame.SUPPORTED_TDMA_VERS
        else:
            return False

    def is_data_mac_layer(self,):
        """Returns TRUE if the first octet in the payload
        indicates this frame is meant for the MAC layer
        """
        return (self.data[0] & HeyMacCmd.PREFIX_MASK) == HeyMacCmd.PREFIX

    def is_data_net_layer(self,):
        """Returns TRUE if the first octet in the payload
        indicates this frame is meant for the NET layer
        """
        return (self.data[0] & APv6Frame.IPHC_PREFIX_MASK) == APv6Frame.APV6_PREFIX


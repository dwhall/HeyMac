"""
Copyright 2018 Dean Hall.  See LICENSE file for details.

HeyMac Frame structure definition
and methods to get/set frame fields.

This file requires the excellent third-party module 'dpkt'
which may be installed via::

    pip3 install dpkt

or::

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
    # HeyMac Protocol IDs
    # 1110 0vvv     HeyMac TDMA, (vvv)ersion
    # 1110 1vvv     HeyMac CSMA, (vvv)ersion
    # 1111 xxxx     HeyMac (RFU: Flood, Extended, etc.)
    PID_HEYMAC   = 0b11100000
    PID_TDMA_VER = 0b00001011
    PID_CSMA_VER = 0b00000000

    # Frame Control Field (Fctl) subfield values
    FCTL_T_SHIFT = 7 #(0:MAC, 1:NET)
    FCTL_L_SHIFT = 6
    FCTL_P_SHIFT = 5
    FCTL_N_SHIFT = 4
    FCTL_D_SHIFT = 3
    FCTL_I_SHIFT = 2
    FCTL_S_SHIFT = 1
    FCTL_M_SHIFT = 0

    # Values for FCTL_T field
    FCTL_TYPE_MAC = 0
    FCTL_TYPE_NET = 1


    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('pid', 'B', PID_HEYMAC | PID_CSMA_VER),
        # The underscore prefix means do not access that field directly.
        # Access properties .fctl, .fctl_t, .fctl_l, etc. instead.
        ('_fctl', 'B', 0),
        # The fields above are guaranteed to be present.
        # Below this are optional fields as indicated by '0s'.
        ('netid', '0s', b''),
        ('daddr', '0s', b''),
        ('hie', '0s', b''),
        ('bie', '0s', b''),
        ('saddr', '0s', b''),
#        ('_', '0s', b''), # use .data to access payload
        ('mic', '0s', b''),
        ('hops', '0s', b''),
        ('txaddr', '0x', b''),
    )

    # Functions to help determine which fields are present
    def _has_netid_field(self,):
        return self.fctl_n != 0
    def _has_daddr_field(self,):
        return self.fctl_d != 0
    def _has_ie_field(self,):
        return self.fctl_i != 0
    def _has_saddr_field(self,):
        return self.fctl_s != 0
    def _has_hops_field(self,):
        return self.fctl_m != 0
    def _has_txaddr_field(self,):
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


    # Getters for the _fctl field
    @property
    def fctl(self,):
        """Gets the full value (all bits) from the Fctl field.
        """
        return self._fctl

    @property
    def fctl_t(self,):
        """Gets the payload type flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_T_SHIFT)

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
        """Sets or clears one of the L,R,N,D,I,S bits
        without modifying the Type bits.
        """
        assert 0 <= val <= 1
        assert 0 <= bit_idx <= 7
        self._fctl &=  ~(1 << bit_idx)
        self._fctl |= (val << bit_idx)

    @fctl_t.setter
    def fctl_t(self, val):
        """Sets the payld Type value in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_T_SHIFT)

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
        # TODO: tolerate TDMA, other versions
        if self.pid != PID_HEYMAC | PID_CSMA_VER:
            raise dpkt.UnpackError()

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

        # The payload comes after SrcAddr.
        # So from here on, we parse the tail of the packet

        if self._has_txaddr_field():
            sz = self._sizeof_addr_field()
            if len(self.data) < sz:
                raise dpkt.NeedData("for txaddr")
            self.txaddr = self.data[-sz:]
            self.data = self.data[: -sz]

        if self._has_hops_field():
            if len(self.data) < 1:
                raise dpkt.NeedData("for txaddr")
            self.hops = self.data[-1:]
            self.data = self.data[:-1]

        # TODO: parse IEs to get MIC

        # At this point self.data should contain the payload

        # Unpack the payload for known frame types
        if self.fctl_t == HeyMacFrame.FCTL_TYPE_MAC:
            try:
                self.payld = HeyMacCmdInstance(self.data)
            except:
                logging.info("invalid MAC cmd %d", self.data[0])
        elif self.fctl_type == HeyMacFrame.FCTL_TYPE_NET:
            try:
                self.payld = APv6Frame(self.data)
            except:
                logging.info("invalid APv6 frame: %b", self.data)


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

        if self.data:
            d.extend(self.data)

        if self.hops:
            if type(hops) is int:
                self.hops = struct.pack("B", self.hops)
            d.append(self.hops)

        if self.txaddr:
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
#        return super().pack_hdr() + bytes(d)
# DEBUG:
        a = super().pack_hdr()
        return a + bytes(d)

    # API
    def is_heymac(self,):
        return self.pid == PID_HEYMAC

    def is_heymac_version_compatible(self,):
        # TODO: make this more robust
        return self.pid == PID_HEYMAC

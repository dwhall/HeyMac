"""
Copyright 2018 Dean Hall.  See LICENSE file for details.

HeyMac Frame structure definition
and methods to get/set frame fields.

This file requires the excellent third-party module 'dpkt'
which may be installed via::

    pip3 install dpkt

"""


import logging

import dpkt # pip install dpkt

from .mac_cmds import *
from .net_frame import APv6Frame


# HeyMac protocol version
HEYMAC_VERSION = 1


class HeyMacFrame(dpkt.Packet):
    """HeyMac frame definition
    """
    # Frame Control Field (Fctl) subfield values
    FCTL_TYPE_MIN = 0b00
    FCTL_TYPE_MAC = 0b01
    FCTL_TYPE_NET = 0b10
    FCTL_TYPE_EXT = 0b11
    FCTL_TYPE_MASK = 0b11000000
    FCTL_TYPE_SHIFT = 6
    FCTL_L_SHIFT = 5
    FCTL_R_SHIFT = 4
    FCTL_N_SHIFT = 3
    FCTL_D_SHIFT = 2
    FCTL_I_SHIFT = 1
    FCTL_S_SHIFT = 0

    # Pend Ver Seq (PVS) subfield values
    PVS_P_MASK = 0b10000000
    PVS_P_SHIFT = 7
    PVS_V_MASK = 0b01110000
    PVS_V_SHIFT = 4
    PVS_S_MASK = 0b00001111
    PVS_S_SHIFT = 0

    __byte_order__ = '!' # Network order
    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties .fctl, .fctl_type, .fctl_l, etc. instead.
        ('_fctl', 'B', FCTL_TYPE_MAC << FCTL_TYPE_SHIFT),
        # Fctl is the only field guaranteed to be present.
        # Below this are optional fields as indicated by '0s'.
        # The underscore prefix means do not access that field directly.
        # Access properties .pend, .ver and .seq, instead.
        ('raddr', '0s', b''),
        ('_pvs', '0s', b''),
        ('exttype', '0s', b''),
        ('netid', '0s', b''),
        ('daddr', '0s', b''),
        ('hie', '0s', b''),
        ('bie', '0s', b''),
        ('saddr', '0s', b''),
    )

    # Functions to help determine which fields are present
    def _has_pvs_field(self,): # PVS exists in all but Min frame types
        return self.fctl_type != HeyMacFrame.FCTL_TYPE_MIN
    def _has_exttype_field(self,): # ExtType exists when Fctl type is Extended
        return self.fctl_type == HeyMacFrame.FCTL_TYPE_EXT
    def _has_raddr_field(self,):
        return self.fctl_r != 0
    def _has_netid_field(self,):
        return self.fctl_n != 0
    def _has_daddr_field(self,):
        return self.fctl_d != 0
    def _has_ie_field(self,):
        return self.fctl_i != 0
    def _has_saddr_field(self,):
        return self.fctl_s != 0

    # Functions to determine size of variable-size fields
    def _sizeof_saddr_field(self,):
        if self._has_saddr_field():
            if self.fctl_l != 0:
                sz = 8
            else:
                sz = 2
        else:
            sz = 0
        return sz

    def _sizeof_daddr_field(self,):
        if self._has_daddr_field():
            if self.fctl_l != 0:
                sz = 8
            else:
                sz = 2
        else:
            sz = 0
        return sz

    def _sizeof_raddr_field(self,):
        if self._has_raddr_field():
            if self.fctl_l != 0:
                sz = 8
            else:
                sz = 2
        else:
            sz = 0
        return sz

    def _sizeof_ie_fields(self,):
        """Returns the sizes of the hIE and bIE fields
        as a tuple (size_of_hIE, size_of_bIE).
        These sizes are dynamic and are calculated by
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
    def fctl_type(self,):
        """Gets the frame type value from the Fctl field.
        """
        return ((self._fctl & HeyMacFrame.FCTL_TYPE_MASK) >> HeyMacFrame.FCTL_TYPE_SHIFT)

    @property
    def fctl_l(self,):
        """Gets the Long address flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_L_SHIFT)

    @property
    def fctl_r(self,):
        """Gets the Resender address present flag from the Fctl field.
        """
        return 1 & (self._fctl >> HeyMacFrame.FCTL_R_SHIFT)

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


    # Setters for the _fctl field
    @fctl.setter
    def fctl(self, val):
        """Sets the full value (all bits) in the Fctl field.
        """
        self._fctl = val

    @fctl_type.setter
    def fctl_type(self, val):
        """Sets the frame type value in the Fctl field.
        If the frame type is not MIN, sets the frame version to HEYMAC_VERSION
        in the PVS field (if the PVS field does not yet exist).
        """
        assert val <= 3, "Invalid frame type"
        self._fctl = (self._fctl & ~HeyMacFrame.FCTL_TYPE_MASK) | (val << HeyMacFrame.FCTL_TYPE_SHIFT)
        if val != HeyMacFrame.FCTL_TYPE_MIN and not hasattr(self, "_pvs"):
            self._pvs = HEYMAC_VERSION << HeyMacFrame.PVS_V_SHIFT

    def _fctl_setter_for_bit(self, val, bit_idx):
        """Sets or clears one of the L,R,N,D,I,S bits
        without modifying the Type bits.
        """
        assert 0 <= val <= 1
        assert 0 <= bit_idx <= 7
        self._fctl &= (HeyMacFrame.FCTL_TYPE_MASK | ~(1 << bit_idx))
        self._fctl |= (val << bit_idx)

    @fctl_l.setter
    def fctl_l(self, val):
        """Sets the Long address flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_L_SHIFT)

    @fctl_r.setter
    def fctl_r(self, val):
        """Sets the Resender address present flag in the Fctl field.
        """
        return self._fctl_setter_for_bit(val, HeyMacFrame.FCTL_R_SHIFT)

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


    # Getters for the _pvs field
    @property
    def pend(self,):
        """Gets the Pending value from the PVS field.
        """
        if self._pvs:
            return (self._pvs[0] & HeyMacFrame.PVS_P_MASK) >> HeyMacFrame.PVS_P_SHIFT
        else:
            return b""

    @property
    def ver(self,):
        """Gets the Version value from the PVS field.
        """
        if self._pvs:
            return (self._pvs[0] & HeyMacFrame.PVS_V_MASK) >> HeyMacFrame.PVS_V_SHIFT
        else:
            return b""

    @property
    def seq(self,):
        """Gets the Sequence value from the PVS field.
        """
        if self._pvs:
            return (self._pvs[0] & HeyMacFrame.PVS_S_MASK) >> HeyMacFrame.PVS_S_SHIFT
        else:
            return b""


    # Setters for the _pvs field
    @pend.setter
    def pend(self, p):
        """Sets the Pending value in the PVS field.
        """
        pvs = 0
        if self._pvs:
            pvs = self._pvs[0] & ~HeyMacFrame.PVS_P_MASK
        if p:
            pvs |= HeyMacFrame.PVS_P_MASK
        self._pvs = pvs.to_bytes(1, "big")

    @seq.setter
    def seq(self, s):
        """Sets the sequence value in the PVS field.
        Also sets the version to HEYMAC_VERSION.
        """
        pvs = 0
        if self._pvs:
            pvs = self._pvs[0] & ~HeyMacFrame.PVS_S_MASK
        pvs |= (HEYMAC_VERSION << HeyMacFrame.PVS_V_SHIFT) | (s << HeyMacFrame.PVS_S_SHIFT)
        self._pvs = pvs.to_bytes(1, "big")


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        super().unpack(buf)

        if self._has_raddr_field():
            sz = self._sizeof_raddr_field()
            if len(self.data) < sz:
                raise dpkt.NeedData("for raddr")
            self.raddr = self.data[0:sz]
            self.data = self.data[sz:]

        if self._has_pvs_field():
            if len(self.data) < 1:
                raise dpkt.NeedData("for pvs")
            self._pvs = self.data[0:1]
            self.data = self.data[1:]

        if self._has_exttype_field():
            if len(self.data) < 1:
                raise dpkt.NeedData("for exttype")
            self.exttype = self.data[0]
            self.data = self.data[1:]

        if self._has_netid_field():
            if len(self.data) < 2:
                raise dpkt.NeedData("for netid")
            self.netid = self.data[0:2]
            self.data = self.data[2:]

        if self._has_daddr_field():
            sz = self._sizeof_daddr_field()
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
            sz = self._sizeof_saddr_field()
            if len(self.data) < sz:
                raise dpkt.NeedData("for saddr")
            self.saddr = self.data[0:sz]
            self.data = self.data[sz:]

        # Unpack the payload for known frame types
        if self.fctl_type == HeyMacFrame.FCTL_TYPE_MAC:
            if self.data:
                if self.data[0] == HeyMacCmdId.SBCN.value:
                    self.data = HeyMacCmdSbcn(self.data)
                elif self.data[0] == HeyMacCmdId.EBCN.value:
                    self.data = HeyMacCmdEbcn(self.data)
                elif self.data[0] == HeyMacCmdId.TXT.value:
                    self.data = HeyMacCmdTxt(self.data)
                else:
                    logging.info("unsupp MAC cmd %f", self.data[0])
            # else:
            #     raise dpkt.NeedData("for MAC payld")
        elif self.fctl_type == HeyMacFrame.FCTL_TYPE_NET:
            if self.data:
                self.data = APv6Frame(self.data)
            # else:
            #     raise dpkt.NeedData("expected APv6 data")


    def pack_hdr(self):
        """Packs header attributes into a bytes object.
        This function is called when bytes() or len() is called
        on an instance of HeyMacFrame.
        """
        d = bytearray()

        # Skip Fctl field for now, insert it at the end of this function

        if self.raddr:
            if type(self.raddr) is int:
                self.raddr = struct.pack("!H", self.raddr)
            len_raddr = len(self.raddr)
            if len_raddr == 8:
                self.fctl_l = 1
                self.fctl_r = 1
            elif len_raddr == 2:
                self.fctl_r = 1
            d.extend(self.raddr)

        # If Fctl indicates PVS should be present
        # and PVS was not set by the caller,
        # set the sequence to zero
        # (which also implicitly sets the version)
        if self._has_pvs_field() and not self._pvs:
            self.seq = 0

        # If PVS was set by caller
        if self._pvs:
            # If Fctl type is MIN, error
            if self.fctl_type == HeyMacFrame.FCTL_TYPE_MIN:
                raise dpkt.PackError("PVS set but Fctl type is MIN")
            if type(self._pvs) is bytes:
                v = self._pvs[0]
            else:
                v = self._pvs
                self._pvs = struct.pack("B", v)
            d.append(v)

        if self._has_exttype_field() and not self.exttype:
            self.exttype = b'\x00'
        if self.exttype or self._has_exttype_field():
            self.fctl_type = HeyMacFrame.FCTL_TYPE_EXT
            if type(self.exttype) is bytes:
                v = self.exttype[0]
            else:
                v = self.exttype
                self.exttype = struct.pack("B", v)
            d.append(v)

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

        return super().pack_hdr() + bytes(d)

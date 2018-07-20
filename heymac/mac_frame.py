import logging
import struct

import dpkt # pip install dpkt

import mac_cmds


# HeyMac protocol version
HEYMAC_VERSION = 1

# Frame Control Field (Fctl) subfield values
FCTL_TYPE_MIN = 0b00
FCTL_TYPE_MAC = 0b01
FCTL_TYPE_NET = 0b10
FCTL_TYPE_EXT = 0b11


class HeyMacFrame(dpkt.Packet):
    """HeyMac frame definition
    """
    __byte_order__ = '!' # Network order
    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties .fctl, .fctl_type, .fctl_l, etc. instead.
        ('_fctl', 'B', FCTL_TYPE_MAC << 6),
        # Fctl is the only field guaranteed to be present.
        # Below this are optional fields as indicated by '0s'.
        # The underscore prefix means do not access that field directly.
        # Access properties .ver and .seq, instead.
        ('_ver_seq', '0s', b''),
        ('raddr', '0s', b''),
        ('exttype', '0s', b''),
        ('netid', '0s', b''),
        ('daddr', '0s', b''),
        ('hie', '0s', b''),
        ('bie', '0s', b''),
        ('saddr', '0s', b''),
    )

    # Functions to help determine which fields are present
    def _has_verseq_field(self,): # VerSeq exists in all but Min frame types
        return self.fctl_type != FCTL_TYPE_MIN
    def _has_raddr_field(self,): # Resender addr exists in all but Min frame types
        return self.fctl_type != FCTL_TYPE_MIN
    def _has_exttype_field(self,): # ExtType exists when Fctl type is Extended
        return self.fctl_type == FCTL_TYPE_EXT
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
        return 0b11 & (self._fctl >> 6)

    @property
    def fctl_l(self,):
        """Gets the Long address flag from the Fctl field.
        """
        return 1 & (self._fctl >> 5)

    @property
    def fctl_n(self,):
        """Gets the NetID present flag from the Fctl field.
        """
        return 1 & (self._fctl >> 4)

    @property
    def fctl_d(self,):
        """Gets the Dest address present flag from the Fctl field.
        """
        return 1 & (self._fctl >> 3)

    @property
    def fctl_i(self,):
        """Gets the IE present flag from the Fctl field.
        """
        return 1 & (self._fctl >> 2)

    @property
    def fctl_s(self,):
        """Gets the Src address present flag from the Fctl field.
        """
        return 1 & (self._fctl >> 1)

    @property
    def fctl_p(self,):
        """Gets the Pending frame flag from the Fctl field.
        """
        return 1 & (self._fctl >> 0)

    # Setters for the _fctl field
    @fctl.setter
    def fctl(self, val):
        """Sets the full value (all bits) in the Fctl field.
        """
        self._fctl = val

    @fctl_type.setter
    def fctl_type(self, val):
        """Sets the frame type value in the Fctl field.
        """
        assert val & 0b11111100 == 0, "Invalid frame type"
        self._fctl = (self._fctl & 0b00111111) | (val << 6)

    @fctl_l.setter
    def fctl_l(self, val):
        """Sets the Long address flag in the Fctl field.
        """
        assert val & ~1 == 0, "Invalid value (must be 0 or 1)"
        self._fctl = (self._fctl & 0b11011111) | (val << 5)

    @fctl_n.setter
    def fctl_n(self, val):
        """Sets the NetID present flag in the Fctl field.
        """
        assert val & ~1 == 0, "Invalid value (must be 0 or 1)"
        self._fctl = (self._fctl & 0b11101111) | (val << 4)


    @fctl_d.setter
    def fctl_d(self, val):
        """Sets the Dest address present flag in the Fctl field.
        """
        assert val & ~1 == 0, "Invalid value (must be 0 or 1)"
        self._fctl = (self._fctl & 0b11110111) | (val << 3)


    @fctl_i.setter
    def fctl_i(self, val):
        """Sets the IEs present flag in the Fctl field.
        """
        assert val & ~1 == 0, "Invalid value (must be 0 or 1)"
        self._fctl = (self._fctl & 0b11111011) | (val << 2)


    @fctl_s.setter
    def fctl_s(self, val):
        """Sets the Source address present flag in the Fctl field.
        """
        assert val & ~1 == 0, "Invalid value (must be 0 or 1)"
        self._fctl = (self._fctl & 0b11111101) | (val << 1)


    @fctl_p.setter
    def fctl_p(self, val):
        """Sets the Pending frame present flag in the Fctl field.
        """
        assert val & ~1 == 0, "Invalid value (must be 0 or 1)"
        self._fctl = (self._fctl & 0b11111110) | (val << 0)


    # Getters for underscore-prefixed fields
    @property
    def ver(self,):
        """Gets the version value from the VerSeq field.
        """
        if self._ver_seq:
            return (self._ver_seq[0] & 0xF0) >> 4
        else:
            return None

    @property
    def seq(self,):
        """Gets the sequence value from the VerSeq field.
        """
        if self._ver_seq:
            return self._ver_seq[0] & 0x0F
        else:
            return None

    # Setters for underscore-prefixed fields
    @seq.setter
    def seq(self, s):
        """Sets the sequence value in the VerSeq field.
        """
        vs = (HEYMAC_VERSION << 4) | (s & 0x0F)
        self._ver_seq = vs.to_bytes(1, "big")


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        super().unpack(buf)

        if self._has_verseq_field():
            if len(self.data) < 1:
                raise dpkt.NeedData("for verseq")
            self._ver_seq = self.data[0:1]
            self.data = self.data[1:]

        if self._has_raddr_field():
            sz = self._sizeof_raddr_field()
            if len(self.data) < sz:
                raise dpkt.NeedData("for raddr")
            self.raddr = self.data[0:sz]
            self.data = self.data[sz:]

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
        if self.fctl_type == FCTL_TYPE_MAC:
            if self.data and self.data[0] == mac_cmds.HeyMacCmdId.SBCN.value:
                self.data = mac_cmds.HeyMacCmdSbcn(self.data)
            elif self.data and self.data[0] == mac_cmds.HeyMacCmdId.EBCN.value:
                self.data = mac_cmds.HeyMacCmdEbcn(self.data)
            elif self.data and self.data[0] == mac_cmds.HeyMacCmdId.TXT.value:
                self.data = mac_cmds.HeyMacCmdTxt(self.data)
            else:
                logging.info("unsupp MAC cmd %f", self.next_tslot)

    def pack_hdr(self):
        """Packs header attributes into a bytes object.
        This function is called when bytes() or len() is called
        on an instance of HeyMacFrame.
        """
        d = []
        nbytes = 0

        # If Fctl indicates VerSeq should be present
        # and VerSeq was not set by the caller,
        # set the sequence to zero
        # (which also implicitly sets the version)
        if self._has_verseq_field() and not self._ver_seq:
            self.seq = 0

        # If VerSeq was set by caller
        if self._ver_seq:
            # If Fctl type is MIN, error
            if not self._has_verseq_field():
                raise dpkt.PackError("VerSeq set but Fctl type is MIN")
            nbytes += 1
            d.append(self._ver_seq)

        if self._has_raddr_field():
            if not self.raddr:
                raise dpkt.PackError("Resender addr not specified")
            len_raddr = len(self.raddr)
            nbytes += len_raddr
            if len_raddr == 8:
                self.fctl_l = 1
            d.append(self.raddr)

        if self._has_exttype_field() and not self.exttype:
            self.exttype = b'\x00'
        if self.exttype or self._has_exttype_field():
            nbytes += 1
            self.fctl_type = FCTL_TYPE_EXT
            d.append(self.exttype)

        if self.netid:
            nbytes += len(self.netid)
            self.fctl_n = 1
            if len(self.netid) != 2:
                raise dpkt.PackError("invalid netid length")
            d.append(self.netid)

        if self.daddr:
            len_daddr = len(self.daddr)
            nbytes += len_daddr
            if len_daddr == 8:
                self.fctl_l = 1
                self.fctl_d = 1
            elif len_daddr == 2:
                self.fctl_d = 1
            d.append(self.daddr)

        # TODO: add IEs

        if self.saddr:
            len_saddr = len(self.saddr)
            nbytes += len_saddr
            if len_saddr == 8:
                self.fctl_l = 1
                self.fctl_s = 1
            elif len_saddr == 2:
                self.fctl_s = 1
            d.append(self.saddr)

        # Repack Fctl because we modify it above
        d.insert(0, super().pack_hdr())

        return b''.join(d)

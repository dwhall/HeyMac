import struct

import dpkt

import mac_cmds


# HeyMac protocol version
HEYMAC_VERSION = 1

# Frame Control Field (Fctl) subfield values
FCTL_TYPE_MIN = 0
FCTL_TYPE_MAC = 0b01 << 6
FCTL_TYPE_NLH = 0b10 << 6
FCTL_TYPE_EXT = 0b11 << 6
FCTL_TYPE_MASK = 0b11 << 6

FCTL_LENCODE_BIT = 1 << 5
FCTL_PEND_BIT = 1 << 4

FCTL_DADDR_MASK = 0b11 << 2
FCTL_DADDR_MODE_NONE = 0
FCTL_DADDR_MODE_64BIT = 0b01 << 2
FCTL_DADDR_MODE_16BIT = 0b10 << 2
FCTL_DADDR_MODE_16BIT_NET = 0b11 << 2

FCTL_SADDR_MASK = 0b11
FCTL_SADDR_MODE_NONE = 0
FCTL_SADDR_MODE_64BIT = 0b01
FCTL_SADDR_MODE_16BIT = 0b10
FCTL_SADDR_MODE_16BIT_NET = 0b11


class HeyMacFrame(dpkt.Packet):
    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('fctl', 'B', 0),
        # Fctl is the only field guaranteed to be present
        # Below this are optional fields
        ('_lencode', '0s', b''),
        ('_ver_seq', '0s', b''), # accessed via .ver and .seq properties
        ('exttype', '0s', b''),
        ('daddr', '0s', b''),
        ('saddr', '0s', b''),
        ('netid', '0s', b''),
    )

    # An instance should override omit_lencode with True
    # to make a packet that omits the lencode field.
    # Fctl will be modified automatically.
    omit_lencode = False

    # Functions to help determine which fields are present
    def _has_lencode_field(self,):
        return (self.fctl &  FCTL_LENCODE_BIT) != 0
    def _has_verseq_field(self,): # VerSeq exists in all but Min frame types
        return (self.fctl & FCTL_TYPE_MASK) != 0
    def _has_exttype_field(self,): # ExtType exists when Fctl type is Extended
        return (self.fctl & FCTL_TYPE_MASK) == FCTL_TYPE_EXT
    def _has_daddr_field(self,):
        return (self.fctl & FCTL_DADDR_MASK) != 0
    def _has_saddr_field(self,):
        return (self.fctl & FCTL_SADDR_MASK) != 0
    def _has_netid_field(self,):
        return (self.fctl & FCTL_DADDR_MASK) == FCTL_DADDR_MODE_16BIT_NET \
            or (self.fctl & FCTL_SADDR_MASK) == FCTL_SADDR_MODE_16BIT_NET

    # Functions to determine size of variable-size fields
    def _sizeof_saddr_field(self,):
        sz = (0, 8, 2, 2)
        sam = (self.fctl & FCTL_SADDR_MASK)
        return sz[sam]
    def _sizeof_daddr_field(self,):
        sz = (0, 8, 2, 2)
        dam = (self.fctl & FCTL_DADDR_MASK) >> 2
        return sz[dam]

    def __len__(self):
        return self._lencode[0] + 1

    # Getters/setters for _<private> fields
    @property
    def ver(self,):
        if self._ver_seq:
            return (self._ver_seq[0] & 0xF0) >> 4
        else:
            return None

    @property
    def seq(self,):
        if self._ver_seq:
            return self._ver_seq[0] & 0x0F
        else:
            return None

    @seq.setter
    def seq(self, s):
        vs = (HEYMAC_VERSION << 4) | (s & 0x0F)
        self._ver_seq = vs.to_bytes(1, "big")

    @property
    def lencode(self,):
        if self._lencode:
            return self._lencode[0]
        else:
            return None

    # Upack/Pack methods needed by dpkt
    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when a HeyMacFrame instance is created
        by passing a bytes object to the constructor
        """
        buflen = len(buf)
        super(HeyMacFrame, self).unpack(buf)

        if self._has_lencode_field():
            if len(self.data) < 1:
                raise dpkt.NeedData('for lencode')
            self._lencode = self.data[0:1]
            self.data = self.data[1:]

        if self._has_verseq_field():
            if len(self.data) < 1:
                raise dpkt.NeedData("for verseq")
            self._ver_seq = self.data[0:1]
            self.data = self.data[1:]

        if self._has_exttype_field():
            if len(self.data) < 1:
                raise dpkt.NeedData("for exttype")
            self.exttype = self.data[0]
            self.data = self.data[1:]

        if self._has_daddr_field():
            sz = self._sizeof_daddr_field()
            if len(self.data) < sz:
                raise dpkt.NeedData("for daddr")
            sz = self._sizeof_daddr_field()
            self.daddr = self.data[0:sz]
            self.data = self.data[sz:]

        if self._has_saddr_field():
            if len(self.data) < 1:
                raise dpkt.NeedData("for saddr")
            sz = self._sizeof_saddr_field()
            self.saddr = self.data[0:sz]
            self.data = self.data[sz:]

        if self._has_netid_field():
            if len(self.data) < 2:
                raise dpkt.NeedData("for netid")
            self.netid = self.data[0:2]
            self.data = self.data[2:]

        # If the Length is known, separate out any excess data (EXPERIMENTAL may want to reject such frames)
        if self._has_lencode_field():
            stated_len = self.lencode + 1
            if buflen > stated_len:
                self.excess = self.data[stated_len - buflen:]
                self.data = self.data[:stated_len - buflen]
                print("Excess data") # TODO: logging

        # Unpack the payload for known frame types
        if self.fctl & FCTL_TYPE_MASK == FCTL_TYPE_MAC:
            if self.data and self.data[0] == 1: #HEYMAC_CMD_BEACON:
                self.data = mac_cmds.HeyMacCmdBeacon(self.data)


    def pack_hdr(self):
        """Packs header attributes into a bytes object.
        This function is called when bytes() or len() is called
        on an instance of HeyMacFrame.
        """
        nbytes = 0
        l = []

        # If Fctl indicates VerSeq should be present
        # and VerSeq was not set by the caller,
        # set the version to fixed value and zero the sequence
        if self._has_verseq_field() and not self._ver_seq:
            self.seq = 0

        # If VerSeq was set by caller
        if self._ver_seq:
            # If Fctl type is MIN, error
            if not self._has_verseq_field():
                raise dpkt.PackError("VerSeq set but Fctl type is MIN")
            nbytes += 1
            l.append(self._ver_seq)

        if self.exttype:
            nbytes += 1
            self.fctl |= FCTL_TYPE_EXT
            l.append(self.exttype)

        if self.daddr:
            len_daddr = len(self.daddr)
            nbytes += len_daddr
            if len_daddr == 8:
                self.fctl |= FCTL_DADDR_MODE_64BIT
            elif len_daddr == 2:
                if self.netid:
                    self.fctl |= FCTL_DADDR_MODE_16BIT_NET
                else:
                    self.fctl |= FCTL_DADDR_MODE_16BIT
            else:
                raise dpkt.PackError("invalid daddr length")
            l.append(self.daddr)

        if self.saddr:
            len_saddr = len(self.saddr)
            nbytes += len_saddr
            if len_saddr == 8:
                self.fctl |= FCTL_SADDR_MODE_64BIT
            elif len_saddr == 2:
                if self.netid:
                    self.fctl |= FCTL_SADDR_MODE_16BIT_NET
                else:
                    self.fctl |= FCTL_SADDR_MODE_16BIT
            else:
                raise dpkt.PackError("invalid saddr length")
            l.append(self.saddr)

        if self.netid:
            nbytes += len(self.netid)
            if len(self.netid) != 2:
                raise dpkt.PackError("invalid netid length")
            l.append(self.netid)

        # Pack Lencode second-to-last so length can be calc'd
        if not self.omit_lencode:
            nbytes += 1
            if hasattr(self, "data") and self.data:
                nbytes += len(self.data)
            if nbytes > 256:
                raise dpkt.PackError("frame length exceeds 256 bytes")
            self._lencode = nbytes.to_bytes(1, "big")
            l.insert(0, self._lencode)
            self.fctl |= FCTL_LENCODE_BIT

        # Pack Fctl last because we modify above
        l.insert(0, super(HeyMacFrame, self).pack_hdr())
        return b''.join(l)

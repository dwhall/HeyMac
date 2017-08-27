"""
Copyright 2017 Dean Hall.  See LICENSE file for details.

HeyMacFrameMaker - HeyMac protocol frame creation
"""


class HeyMacFrameMaker(object):
    """Class and methods that create a HeyMac frame and fill its fields.
    The frame is comprised of the header and payload, both are variable-length.
    When creating a frame, the data accumulates in a dict
    where each field is a key in the dict and the value holds the field data.
    Valid field names are listed in FIELD_NAMES.
    
    To serialize the frame for transmission, cast the instance to a string::

        str(frame_instance)

    If you need finer control over the field options than str() provides,
    first call to_bytearray() with the desired arguments.
    """

    # HeyMac protocol version number
    VERSION = 1

    # Shorthand field names.  Used with any field_name argument
    FIELD_NAMES = (
        "fctl",     # Frame Control
        "len",      # Length
        "exttype",  # Extended Type
        "daddr",    # Destination Address
        "saddr",    # Source Address
#        "netid",    # Network ID
        "payld"     # Payload
        )

    # Shorthand values for fctl_type arguments (Fctl's Type subfield)
    FCTL_TYPES = {
        "min" : 0b00 << 6,  # Minimum sized frame
        "mac" : 0b01 << 6,  # HeyMac command frame
        "nlh" : 0b10 << 6,  # Next Layer Higher (NLH) frame
        "ext" : 0b11 << 6,  # Extended Type frame
        }

    # Shorthand values for Address Modes, DAM and SAM
    ADDR_MODES = {
        "absent" : 0b00,    # Address field is absent
        "64b" : 0b01,       # Address field is 8 octets
        "16b" : 0b10,       # Address field is 2 octets
        "16b+netid" : 0b11, # Address field is 2 octets
                            # and netid field is present
        }

    # Frame Control field bit positions
    FCTL_LEN_BIT = 1 << 5
    FCTL_PEND_BIT = 1 << 4
    FCTL_TYPE_SHIFT = 6
    FCTL_DAM_SHIFT = 2


    def __init__(self, fctl_type='min', **field_names):
        """Compose a frame by setting a value for each field.
        The Frame Control (fctl) and Length (len) fields will be calculated;
        you should not pass them as arguments.
        """
        assert fctl_type in HeyMacFrameMaker.FCTL_TYPES
        if fctl_type == 'ext':
            assert 'exttype' in field_names, \
                "When fctl_type is 'ext', the 'exttype' field must be present."

        self.fctl_type = fctl_type
        self.fctl_dam = 0
        self.fctl_sam = 0
        self.fields = {
            'daddr': "", 
            'saddr': "",
            }

        for field_name, field_val in field_names.items():
            self.add_field(field_name, field_val)


    def add_field(self, field_name, field_val):
        """Adds a field to the frame being composed.
        Validates the type and value of the field value.
        """
        assert field_name in HeyMacFrameMaker.FIELD_NAMES
        assert field_name is not "fctl"
        assert field_name is not "len"

        if field_name is "ver" or field_name is "seq":
            assert type(field_val) is int
            assert field_val >= 0 and field_val <=16
            self.fields[field_name] = field_val

        elif field_name is "exttype":
            assert type(field_val) is int
            assert field_val >= 0 and field_val <= 255 
            self.fields[field_name] = field_val

        elif field_name is "daddr":
            assert type(field_val) is bytes
            len_field_val = len(field_val)
            assert len_field_val in (0,2,8)
            self.fields[field_name] = field_val
            if len_field_val == 0:
                self.fctl_dam = HeyMacFrameMaker.ADDR_MODES['absent']
            elif len_field_val == 2:
                self.fctl_dam = HeyMacFrameMaker.ADDR_MODES['16b']
            elif len_field_val == 8:
                self.fctl_dam = HeyMacFrameMaker.ADDR_MODES['64b']

        elif field_name is "saddr":
            assert type(field_val) is bytes
            len_field_val = len(field_val)
            assert len_field_val in (0,2,8)
            self.fields[field_name] = field_val
            if len_field_val == 0:
                self.fctl_sam = HeyMacFrameMaker.ADDR_MODES['absent']
            elif len_field_val == 2:
                self.fctl_sam = HeyMacFrameMaker.ADDR_MODES['16b']
            elif len_field_val == 8:
                self.fctl_sam = HeyMacFrameMaker.ADDR_MODES['64b']

        elif field_name is "netid":
            # assert type(field_val) is int
            # assert field_val >= 0 and field_val <= 65535
            # self.fields[field_name] = field_val
            assert False, "This field is not yet supported"

        elif field_name is "payld":
            assert type(field_val) is bytes
            self.fields[field_name] = field_val


    def to_bytearray(self, add_len=True, fctl_pend=0, seq=0):
        """Sets the Pending and Sequence subfields and
        serializes the frame's fields into a bytearray.
        Returns the bytearray
        """

        self.fields['fctl'] = ( HeyMacFrameMaker.FCTL_TYPES[self.fctl_type]
                              | self.fctl_dam << HeyMacFrameMaker.FCTL_DAM_SHIFT
                              | self.fctl_sam << 0
                              )
        if add_len:
            self.fields['fctl'] |= HeyMacFrameMaker.FCTL_LEN_BIT

        b = bytearray()
        b.append(self.fields['fctl'])

        # If the Pending bit should be set in Fctl
        if fctl_pend: 
            b[-1] |= HeyMacFrameMaker.FCTL_PEND_BIT

        # If frame type is not min, append the Version and Sequence field
        if self.fctl_type is not "min":
            b.append(HeyMacFrameMaker.VERSION << 4 | seq & 0x0f)

        if 'exttype' in self.fields:
            b.append(self.fields['exttype'])
        if "daddr" in self.fields:
            b.extend(self.fields['daddr'])
        if "saddr" in self.fields:
            b.extend(self.fields['saddr'])
        # if "netid" in self.fields:
        #     b.extend(self.fields['netid'])
        if "payld" in self.fields:
            b.extend(self.fields['payld'])

        # Calculate, insert and validate frame length.
        # len(b) will be one less than length of frame
        # after the insert(), which is the desired value for thie field
        if add_len:
            b.insert(1, len(b))
        assert len(b) <= 256, "Frame length exceeds 256 bytes"

        return b


    def __str__(self,):
        """Returns the serialized frame as a string.
        """
        b = self.to_bytearray()
        return "".join(map(chr, b))


if __name__ == "__main__":
    #Runs some tests on frame composition.

    # The smallest frame is a single zero byte
    f = HeyMacFrameMaker()
    b = f.to_bytearray(add_len=False)
    s = "".join(map(chr, b))
    assert s == "\x00"

    # Another small, useless frame
    f = HeyMacFrameMaker()
    b = f.to_bytearray()
    s = "".join(map(chr, b))
    assert s == "\x20\x01"

    f = HeyMacFrameMaker(
        fctl_type = 'min',
        saddr = "\x01\x02\x03\x04\x05\x06\x07\x08",
        )
    assert str(f) == "\x21\x09\x01\x02\x03\x04\x05\x06\x07\x08"

    f = HeyMacFrameMaker(
        fctl_type = 'mac',
        daddr = "\xff\xff",
        saddr = "\xab\xcd",
        payld = "hello world"
        )
    assert str(f) == "\x6A\x11\x10\xff\xff\xab\xcdhello world"

    f = HeyMacFrameMaker(
        fctl_type = 'mac',
        daddr = "\xff\xff\xff\xff\xff\xff\xff\xff",
        saddr = "\xab\xcd\xef\x01\x02\x03\x04\x05",
        payld = "hi"
        )
    assert str(f) == "\x65\x14\x10\xff\xff\xff\xff\xff\xff\xff\xff\xab\xcd\xef\x01\x02\x03\x04\x05hi"

    f = HeyMacFrameMaker(
        fctl_type = 'nlh',
        payld = "ipv6_hdr_compression"
        )
    assert str(f) == "\xA0\x16\x10ipv6_hdr_compression"

    f = HeyMacFrameMaker(
        fctl_type = 'ext',
        exttype = 42, # ExtType values are undefined.  This is arbitrary value
        payld = "6x7"
        )
    assert str(f) == "\xE0\x06\x10\x2A6x7"

    print("Frame composition tests: PASS")

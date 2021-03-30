import unittest

from heymac.net import honr


class TestNetHonr(unittest.TestCase):
    def test_to_internal_repr(self,):
        # Bad data type
        with self.assertRaises(AssertionError): honr.to_internal_repr([0, 0])
        # Good data types
        self.assertEqual(honr.to_internal_repr(b"\x01\x02"), bytearray([0, 1, 0, 2]))
        self.assertEqual(honr.to_internal_repr(b"\x01\x02\x03\x04\x05\x06\x07\x08"), bytearray([0, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7, 0, 8,]))


    def test_to_external_addr(self,):
        with self.assertRaises(AssertionError): honr.to_external_addr([0, 0])
        self.assertEqual(honr.to_external_addr(bytearray([0, 1, 0, 2])), b"\x01\x02")
        self.assertEqual(honr.to_external_addr(bytearray([0, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7, 0, 8,])), b"\x01\x02\x03\x04\x05\x06\x07\x08")


    def test_get_nearest_common_ancestor(self,):
        # Happy cases
        self.assertEqual(honr.get_nearest_common_ancestor(b"\x00\x00", b"\x00\x00"), b"\x00\x00")
        self.assertEqual(honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(honr.get_nearest_common_ancestor(b"\x10\x00", b"\x20\x00"), b"\x00\x00")
        self.assertEqual(honr.get_nearest_common_ancestor(b"\x10\x00\x00\x00\x00\x00\x00\x00", b"\x20\x00\x00\x00\x00\x00\x00\x00"), b"\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(honr.get_nearest_common_ancestor(b"\x11\x10", b"\x11\x00"), b"\x11\x00")
        self.assertEqual(honr.get_nearest_common_ancestor(b"\x22\x20\x00\x00\x00\x00\x00\x00", b"\x22\x00\x00\x00\x00\x00\x00\x00"), b"\x22\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(honr.get_nearest_common_ancestor(b"\x11\x10", b"\x1E\xB0"), b"\x10\x00")
        self.assertEqual(honr.get_nearest_common_ancestor(b"\x11\x10\x00\x00\x00\x00\x00\x00", b"\x1E\xB0\x00\x00\x00\x00\x00\x00"), b"\x10\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(honr.get_nearest_common_ancestor(b"\xA1\x23", b"\xBB\x29"), b"\x00\x00")
        # Bad addresses
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x10\x00\x00\x00", b"\x00\x00")
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x01\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x00\x00", b"\x10\x00\x00\x00")
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x01\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x00\x00", b"\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00", b"\x00\x00")
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x00\x00\x00\x01", b"\x00\x00")
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x00\x00", b"\x00\x00\x00\x01")
        with self.assertRaises(AssertionError): honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01")


    def test_get_parent(self,):
        # Ensure a constant
        self.assertEqual(honr.ROOT2, b"\x00\x00")
        # Parent of Root is None
        self.assertEqual(honr.get_parent(b"\x00\x00"), None)
        # Parent matches
        self.assertEqual(honr.get_parent(b"\x10\x00"), b"\x00\x00")
        self.assertEqual(honr.get_parent(b"\x38\xA0"), b"\x38\x00")
        self.assertEqual(honr.get_parent(b"\xEE\xEE"), b"\xEE\xE0")
        # Parent mismatches
        self.assertNotEqual(honr.get_parent(b"\x00\x00"), b"\x00\x00")
        self.assertNotEqual(honr.get_parent(b"\x20\x00"), b"\x10\x00")
        self.assertNotEqual(honr.get_parent(b"\x21\x00"), b"\x10\x00")
        self.assertNotEqual(honr.get_parent(b"\xEE\x00"), b"\xEE\x00")
        self.assertNotEqual(honr.get_parent(b"\xEE\x00"), b"\x0F\x00")
        self.assertNotEqual(honr.get_parent(b"\x38\xC9"), b"\xC9\x00")
        # Invalid addresses
        with self.assertRaises(AssertionError): honr.get_parent(b"\xFF\x0F")
        with self.assertRaises(AssertionError): honr.get_parent(b"\x0F\x00")
        with self.assertRaises(AssertionError): honr.get_parent(b"\x1F\x30")


    def test_get_rank(self,):
        # Happy cases
        self.assertEqual(honr.get_rank(b"\x00\x00"), 0)
        self.assertEqual(honr.get_rank(b"\x10\x00"), 1)
        self.assertEqual(honr.get_rank(b"\xF0\x00"), 1)
        self.assertEqual(honr.get_rank(b"\x22\x00"), 2)
        self.assertEqual(honr.get_rank(b"\xCC\xC0"), 3)
        self.assertEqual(honr.get_rank(b"\xDD\xD9"), 4)
        self.assertEqual(honr.get_rank(b"\xDD\xDF"), 4)
        self.assertEqual(honr.get_rank(b"\xFF\xFF"), 4)
        # Rank mismatches
        self.assertNotEqual(honr.get_rank(b"\x00\x00"), 1)
        self.assertNotEqual(honr.get_rank(b"\xEE\xEE"), 2)
        # Invalid addresses
        with self.assertRaises(AssertionError): honr.get_rank(b"\xF0\xF0")
        with self.assertRaises(AssertionError): honr.get_rank(b"\x0F\x00")
        with self.assertRaises(AssertionError): honr.get_rank(b"\x00\xF0")
        with self.assertRaises(AssertionError): honr.get_rank(b"\x00\x0F")


    def test_is_addr_valid(self,):
        # Valid addresses
        self.assertTrue(honr.is_addr_valid(b"\x00\x00"))
        self.assertTrue(honr.is_addr_valid(b"\x00\x00\x00\x00\x00\x00\x00\x00"))
        self.assertTrue(honr.is_addr_valid(b"\x10\x00"))
        self.assertTrue(honr.is_addr_valid(b"\x10\x00\x00\x00\x00\x00\x00\x00"))
        self.assertTrue(honr.is_addr_valid(b"\x1E\xEE"))
        # Valid broadcast addresses
        self.assertTrue(honr.is_addr_valid(b"\xF0\x00"))
        self.assertTrue(honr.is_addr_valid(b"\x1F\x00"))
        self.assertTrue(honr.is_addr_valid(b"\x2F\xF0"))
        self.assertTrue(honr.is_addr_valid(b"\x32\xFF"))
        self.assertTrue(honr.is_addr_valid(b"\xFF\xFF"))
        # Invalid addresses
        # zero left of non-zero
        self.assertFalse(honr.is_addr_valid(b"\x00\x10"))
        self.assertFalse(honr.is_addr_valid(b"\x00\x00\x00\x00\x00\x00\x00\x01"))
        self.assertFalse(honr.is_addr_valid(b"\x1E\x0E"))
        self.assertFalse(honr.is_addr_valid(b"\x1F\x01"))
        # addr wrong size
        self.assertFalse(honr.is_addr_valid(b"\x10\x00\x00"))
        self.assertFalse(honr.is_addr_valid(b"\x10\x00\x00\x00\x00\x00\x00\x00\x00"))
        # bad datatype
        self.assertFalse(honr.is_addr_valid(0x0000))
        self.assertFalse(honr.is_addr_valid("\x10\x00"))
        # invalid broadcast
        self.assertFalse(honr.is_addr_valid(b"\x00\x0F"))
        self.assertFalse(honr.is_addr_valid(b"\x1F\x0F"))
        self.assertFalse(honr.is_addr_valid(b"\xF1\xF0"))


    def test_is_addr_valid_bcast(self,):
        # Valid broadcast addresses
        self.assertTrue(honr.is_addr_valid_bcast(b"\xF0\x00"))
        self.assertTrue(honr.is_addr_valid_bcast(b"\x1F\x00"))
        self.assertTrue(honr.is_addr_valid_bcast(b"\x2F\xF0"))
        self.assertTrue(honr.is_addr_valid_bcast(b"\x32\xFF"))
        self.assertTrue(honr.is_addr_valid_bcast(b"\xFF\xFF"))
        # Invalid addresses
        # zero left of non-zero
        self.assertFalse(honr.is_addr_valid_bcast(b"\x00\x10"))
        self.assertFalse(honr.is_addr_valid_bcast(b"\x00\x00\x00\x00\x00\x00\x00\x01"))
        self.assertFalse(honr.is_addr_valid_bcast(b"\x1E\x0E"))
        self.assertFalse(honr.is_addr_valid_bcast(b"\x1F\x01"))
        # addr wrong size
        self.assertFalse(honr.is_addr_valid_bcast(b"\x10\x00\x00"))
        self.assertFalse(honr.is_addr_valid_bcast(b"\x10\x00\x00\x00\x00\x00\x00\x00\x00"))
        # bad datatype
        self.assertFalse(honr.is_addr_valid_bcast(0x0000))
        self.assertFalse(honr.is_addr_valid_bcast("\x10\x00"))
        # invalid broadcast
        self.assertFalse(honr.is_addr_valid_bcast(b"\x00\x0F"))
        self.assertFalse(honr.is_addr_valid_bcast(b"\x1F\x0F"))
        self.assertFalse(honr.is_addr_valid_bcast(b"\xF1\xF0"))


    def test_is_addr_valid_node(self,):
        # Valid addresses
        self.assertTrue(honr.is_addr_valid(b"\x00\x00"))
        self.assertTrue(honr.is_addr_valid(b"\x00\x00\x00\x00\x00\x00\x00\x00"))
        self.assertTrue(honr.is_addr_valid(b"\x10\x00"))
        self.assertTrue(honr.is_addr_valid(b"\x10\x00\x00\x00\x00\x00\x00\x00"))
        self.assertTrue(honr.is_addr_valid(b"\x1E\xEE"))
        # Valid broadcast addresses
        self.assertFalse(honr.is_addr_valid_node(b"\xF0\x00"))
        self.assertFalse(honr.is_addr_valid_node(b"\x1F\x00"))
        self.assertFalse(honr.is_addr_valid_node(b"\x2F\xF0"))
        self.assertFalse(honr.is_addr_valid_node(b"\x32\xFF"))
        self.assertFalse(honr.is_addr_valid_node(b"\xFF\xFF"))
        # Invalid addresses
        # zero left of non-zero
        self.assertFalse(honr.is_addr_valid_node(b"\x00\x10"))
        self.assertFalse(honr.is_addr_valid_node(b"\x00\x00\x00\x00\x00\x00\x00\x01"))
        self.assertFalse(honr.is_addr_valid_node(b"\x1E\x0E"))
        self.assertFalse(honr.is_addr_valid_node(b"\x1F\x01"))
        # addr wrong size
        self.assertFalse(honr.is_addr_valid_node(b"\x10\x00\x00"))
        self.assertFalse(honr.is_addr_valid_node(b"\x10\x00\x00\x00\x00\x00\x00\x00\x00"))
        # bad datatype
        self.assertFalse(honr.is_addr_valid_node(0x0000))
        self.assertFalse(honr.is_addr_valid_node("\x10\x00"))
        # invalid broadcast
        self.assertFalse(honr.is_addr_valid_node(b"\x00\x0F"))
        self.assertFalse(honr.is_addr_valid_node(b"\x1F\x0F"))
        self.assertFalse(honr.is_addr_valid_node(b"\xF1\xF0"))


if __name__ == '__main__':
    unittest.main()

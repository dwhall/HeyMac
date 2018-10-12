import unittest

import dll_honr


class TestDllHonr(unittest.TestCase):
    def test__to_internal_repr(self,):
        with self.assertRaises(AssertionError): dll_honr._to_internal_repr([0, 0])
        self.assertEqual(dll_honr._to_internal_repr(b"\x01\x02"), bytearray([0, 1, 0, 2]))
        self.assertEqual(dll_honr._to_internal_repr(b"\x01\x02\x03\x04\x05\x06\x07\x08"), bytearray([0, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7, 0, 8,]))


    def test__to_external_addr(self,):
        with self.assertRaises(AssertionError): dll_honr._to_external_addr([0, 0])
        self.assertEqual(dll_honr._to_external_addr(bytearray([0, 1, 0, 2])), b"\x01\x02")
        self.assertEqual(dll_honr._to_external_addr(bytearray([0, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7, 0, 8,])), b"\x01\x02\x03\x04\x05\x06\x07\x08")


    def test_get_nearest_common_ancestor(self,):
        # Happy cases
        self.assertEqual(dll_honr.get_nearest_common_ancestor(b"\x00\x00", b"\x00\x00"), b"\x00\x00")
        self.assertEqual(dll_honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00"), b"\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(dll_honr.get_nearest_common_ancestor(b"\x10\x00", b"\x20\x00"), b"\x00\x00")
        self.assertEqual(dll_honr.get_nearest_common_ancestor(b"\x10\x00\x00\x00\x00\x00\x00\x00", b"\x20\x00\x00\x00\x00\x00\x00\x00"), b"\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(dll_honr.get_nearest_common_ancestor(b"\x11\x10", b"\x11\x00"), b"\x11\x00")
        self.assertEqual(dll_honr.get_nearest_common_ancestor(b"\x22\x20\x00\x00\x00\x00\x00\x00", b"\x22\x00\x00\x00\x00\x00\x00\x00"), b"\x22\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(dll_honr.get_nearest_common_ancestor(b"\x11\x10", b"\x1E\xB0"), b"\x10\x00")
        self.assertEqual(dll_honr.get_nearest_common_ancestor(b"\x11\x10\x00\x00\x00\x00\x00\x00", b"\x1E\xB0\x00\x00\x00\x00\x00\x00"), b"\x10\x00\x00\x00\x00\x00\x00\x00")
        self.assertEqual(dll_honr.get_nearest_common_ancestor(b"\xA1\x23", b"\xBB\x29"), b"\x00\x00")
        # Bad addresses
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x10\x00\x00\x00", b"\x00\x00")
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x01\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x00\x00", b"\x10\x00\x00\x00")
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x01\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x00\x00", b"\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00", b"\x00\x00")
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x00\x00\x00\x01", b"\x00\x00")
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01", b"\x00\x00\x00\x00\x00\x00\x00\x00")
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x00\x00", b"\x00\x00\x00\x01")
        with self.assertRaises(AssertionError): dll_honr.get_nearest_common_ancestor(b"\x00\x00\x00\x00\x00\x00\x00\x00", b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01")


    def test_get_parent(self,):
        # Ensure a constant
        self.assertEqual(dll_honr.ROOT2, b"\x00\x00")
        # Parent of Root is None
        self.assertEqual(dll_honr.get_parent(b"\x00\x00"), None)
        # Parent matches
        self.assertEqual(dll_honr.get_parent(b"\x10\x00"), b"\x00\x00")
        self.assertEqual(dll_honr.get_parent(b"\x38\xA0"), b"\x38\x00")
        self.assertEqual(dll_honr.get_parent(b"\xFF\xFF"), b"\xFF\xF0")
        # Parent mismatches
        self.assertNotEqual(dll_honr.get_parent(b"\x00\x00"), b"\x00\x00")
        self.assertNotEqual(dll_honr.get_parent(b"\x20\x00"), b"\x10\x00")
        self.assertNotEqual(dll_honr.get_parent(b"\x21\x00"), b"\x10\x00")
        self.assertNotEqual(dll_honr.get_parent(b"\xFF\x00"), b"\xFF\x00")
        self.assertNotEqual(dll_honr.get_parent(b"\xFF\x00"), b"\x0F\x00")
        self.assertNotEqual(dll_honr.get_parent(b"\x38\xC9"), b"\xC9\x00")


    def test_get_rank(self,):
        # Happy cases
        self.assertEqual(dll_honr.get_rank(b"\x00\x00"), 0)
        self.assertEqual(dll_honr.get_rank(b"\x10\x00"), 1)
        self.assertEqual(dll_honr.get_rank(b"\x22\x00"), 2)
        self.assertEqual(dll_honr.get_rank(b"\xCC\xC0"), 3)
        self.assertEqual(dll_honr.get_rank(b"\xFF\xFF"), 4)
        # Rank mismatches
        self.assertNotEqual(dll_honr.get_rank(b"\x00\x00"), 1)
        self.assertNotEqual(dll_honr.get_rank(b"\xFF\xFF"), 2)


    def test_get_route(self,):
        # Happy cases
        self.assertEqual(dll_honr.get_route(b"\x00\x00", b"\x00\x00"), [b"\x00\x00"])
        self.assertEqual(dll_honr.get_route(b"\x10\x00", b"\x00\x00"), [b"\x10\x00", b"\x00\x00"])
        self.assertEqual(dll_honr.get_route(b"\x00\x00", b"\x10\x00"), [b"\x00\x00", b"\x10\x00"])
        self.assertEqual(dll_honr.get_route(b"\x11\x00", b"\x10\x00"), [b"\x11\x00", b"\x10\x00"])
        self.assertEqual(dll_honr.get_route(b"\xA0\x00", b"\xB0\x00"), [b"\xA0\x00", b"\x00\x00", b"\xB0\x00"])
        self.assertEqual(dll_honr.get_route(b"\xA1\x23", b"\xBB\x29"),
                                            [b"\xA1\x23", b"\xA1\x20", b"\xA1\x00", b"\xA0\x00",
                                            b"\x00\x00",
                                            b"\xB0\x00", b"\xBB\x00", b"\xBB\x20", b"\xBB\x29", ])


    def test_is_addr_valid(self,):
        # Valid addresses
        self.assertTrue(dll_honr.is_addr_valid(b"\x00\x00"))
        self.assertTrue(dll_honr.is_addr_valid(b"\x00\x00\x00\x00\x00\x00\x00\x00"))
        self.assertTrue(dll_honr.is_addr_valid(b"\x10\x00"))
        self.assertTrue(dll_honr.is_addr_valid(b"\x10\x00\x00\x00\x00\x00\x00\x00"))
        self.assertTrue(dll_honr.is_addr_valid(b"\x1E\xEE"))
        self.assertTrue(dll_honr.is_addr_valid(b"\x1F\xFF"))
        # Invalid addresses
        # zero left of non-zero
        self.assertFalse(dll_honr.is_addr_valid(b"\x00\x10"))
        self.assertFalse(dll_honr.is_addr_valid(b"\x00\x00\x00\x00\x00\x00\x00\x01"))
        self.assertFalse(dll_honr.is_addr_valid(b"\x1E\x0E"))
        self.assertFalse(dll_honr.is_addr_valid(b"\x1F\x01"))
        # addr wrong size
        self.assertFalse(dll_honr.is_addr_valid(b"\x10\x00\x00"))
        self.assertFalse(dll_honr.is_addr_valid(b"\x10\x00\x00\x00\x00\x00\x00\x00\x00"))
        # bad datatype
        self.assertFalse(dll_honr.is_addr_valid(0x0000))
        self.assertFalse(dll_honr.is_addr_valid("\x10\x00"))


    def test_should_route(self,):
        # Routing
        self.assertTrue(dll_honr.should_route(b"\x11\x00", b"\x00\x00", b"\x10\x00"))
        self.assertTrue(dll_honr.should_route(b"\x11\x11", b"\x00\x00", b"\x11\x10"))
        # No routing, already at destination
        self.assertFalse(dll_honr.should_route(b"\x00\x00", b"\x00\x00", b"\x00\x00"))
        self.assertFalse(dll_honr.should_route(b"\x10\x00", b"\x00\x00", b"\x00\x00"))
        self.assertFalse(dll_honr.should_route(b"\x10\x00", b"\x11\x00", b"\x11\x00"))
        # No routing, loc is not along path
        self.assertFalse(dll_honr.should_route(b"\x00\x00", b"\x10\x00", b"\x20\x00"))
        self.assertFalse(dll_honr.should_route(b"\x11\x00", b"\x00\x00", b"\x20\x00"))
        # No routing, loc is in path, but not next
        self.assertFalse(dll_honr.should_route(b"\x11\x11", b"\x00\x00", b"\x10\x00"))
        # No routing, resender is self (something went wrong)
        self.assertFalse(dll_honr.should_route(b"\x10\x00", b"\x00\x00", b"\x10\x00"))
        # TODO: cases with 8-octet addresses


if __name__ == '__main__':
    unittest.main()

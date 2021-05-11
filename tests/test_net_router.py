import unittest

from heymac.net import route


class TestNetRouter(unittest.TestCase):

    def test_get_route(self):
        # Happy cases
        self.assertEqual(route.get_route(b"\x00\x00", b"\x00\x00"), [b"\x00\x00"])
        self.assertEqual(route.get_route(b"\x10\x00", b"\x00\x00"), [b"\x10\x00", b"\x00\x00"])
        self.assertEqual(route.get_route(b"\x00\x00", b"\x10\x00"), [b"\x00\x00", b"\x10\x00"])
        self.assertEqual(route.get_route(b"\x11\x00", b"\x10\x00"), [b"\x11\x00", b"\x10\x00"])
        self.assertEqual(route.get_route(b"\xA0\x00", b"\xB0\x00"), [b"\xA0\x00", b"\x00\x00", b"\xB0\x00"])
        self.assertEqual(route.get_route(b"\xA1\x23", b"\xBB\x29"),
                                            [b"\xA1\x23", b"\xA1\x20", b"\xA1\x00", b"\xA0\x00",
                                            b"\x00\x00",
                                            b"\xB0\x00", b"\xBB\x00", b"\xBB\x20", b"\xBB\x29", ])


    def test_should_route(self):
        # Routing
        self.assertTrue(route.should_route(b"\x11\x00", b"\x00\x00", b"\x10\x00"))
        self.assertTrue(route.should_route(b"\x11\x11", b"\x00\x00", b"\x11\x10"))
        # No routing, already at destination
        self.assertFalse(route.should_route(b"\x00\x00", b"\x00\x00", b"\x00\x00"))
        self.assertFalse(route.should_route(b"\x10\x00", b"\x00\x00", b"\x00\x00"))
        self.assertFalse(route.should_route(b"\x10\x00", b"\x11\x00", b"\x11\x00"))
        # No routing, loc is not along path
        self.assertFalse(route.should_route(b"\x00\x00", b"\x10\x00", b"\x20\x00"))
        self.assertFalse(route.should_route(b"\x11\x00", b"\x00\x00", b"\x20\x00"))
        # No routing, loc is in path, but not next
        self.assertFalse(route.should_route(b"\x11\x11", b"\x00\x00", b"\x10\x00"))
        # No routing, resender is self (something went wrong)
        self.assertFalse(route.should_route(b"\x10\x00", b"\x00\x00", b"\x10\x00"))
        # TODO: cases with 8-octet addresses


if __name__ == '__main__':
    unittest.main()

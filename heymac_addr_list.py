import unittest

"""HeyMac Address operations
An address is of type bytes in order to be immutable.
In this file, each byte holds only a nibble (4-bits) of address
to make it easier to manipulate each nibble separately.
These operations are meant to show how easy it is to route within a DAG of nodes with HONR addresses.

In a DAG, routing is either "up" or "down".
Upward routes travel toward the DAG's root.
Downward routes travel toward a leaf node.

The Root enjoys the all-zero address: 0000.
The nodes that have the Root as their parent (a.k.a. Rank 1 nodes), have all nibbles set to zero except the leftmost one.
Rank 2 nodes have theif left-most nibble set to match their Rank 1 parent's first nibble
and their second-to-left-most nibble set to uniquely identify themselves.

Root:                       0000
                            |
            +-------+-------+-------+-------+-------+
            |       |       |       |       |       |
Rank 1:     1000    2000    5000    7000    A000    C000
            |                       |               |
            +-------+       +-------+               +
            |       |       |       |               |
Rank 2:     1100    1800    7200    7C00            C500
"""

class HeyMacAddr(object):

    def __init__(self, s):
        self.data = list(s)
        assert self._is_valid()


    def _is_valid(self,):
        """Returns True if the given address meets all critera for a valid address.
        Address must be 4 or 16 nibbles (16 or 64 bits)
        Address values must be nibble-sized
        A zero must not be left (more significant posn) of a non-zero
        """
        valid = True

        # Address must be 4 or 16 nibbles (16 or 64 bits)
        if len(self.data) not in (4, 16):
            valid = False

        else:
            leftzero = -1
            for i in range(len(self.data)):

                # All values must be nibble-sized
                if self.data[i] >= 16:
                    valid = False

                # Save the index of the left-most zero
                if leftzero < 0 and self.data[i] == 0:
                    leftzero = i
                    continue

                # Everything right of the left-most zero must be a zero
                if leftzero >= 0 and self.data[i] != 0:
                    valid = False

        return valid


    def get_nearest_common_ancestor(self, other):
        """Returns the address of the Nearest Common Ancestor
        which connects this and the other node in a DAG.
        """
        assert len(self.data) == len(other.data)

        differ = False

        # Copy the nibble to the NCA when it is the same in both (LtoR)
        nca = []
        for i in range(len(self.data)):
            if self.data[i] == other.data[i]:
                if differ:
                    nca.append(0)
                else:
                    nca.append(self.data[i])
            else:
                nca.append(0)
                differ = True

        return HeyMacAddr(nca)


    def get_next_addr(self, dst):
        """Returns the address of the next node on the route to dest.
        Assumes this node should route the packet.
        """
        route_dir = self.get_route_dir(dst)
        leftzero = self.data.index(0)
        if leftzero == -1:
            leftzero = len(self.data)
        next_addr = [0,] * len(self.data)

        # Upward routes have fewer nonzero digits
        if route_dir == "up":
            next_addr[0:leftzero - 1] = self.data[0:leftzero - 1]

        # Downward routes have more nonzero digits
        elif route_dir == "down":
            next_addr[0:leftzero + 1] = dst[0:leftzero + 1]
        return bytes(next_addr)


    def get_route(src, dst):
        """Returns the sequence of nodes from src to dst, inclusive
        as a list of addresses (bytes of nibbles).
        """
        # No need to assert-check src and dst, get_nearest_common_ancestor() will do that
        route = []
        nca = get_nearest_common_ancestor(src, dst)
        cur = bytearray(src)
        leftzero = cur.find(0)
        if leftzero == -1:
            leftzero = len(src)

        while cur != nca:
            route.append(bytes(cur))
            leftzero -= 1
            cur[leftzero] = 0
        route.append(bytes(nca))
        while cur != dst:
            cur[leftzero] = dst[leftzero]
            route.append(bytes(cur))
            leftzero += 1
        return route


    def get_route_dir(myaddr, dst):
        """Returns the direction to route the packet.
        If this node's address is the dst, routing is done (None).
        If this node's address matches the destination up to
        this node's left-most zero, route down; else route up
        """
        assert is_addr_valid(myaddr)
        assert is_addr_valid(dst)
        assert len(myaddr) == len(dst)

        route_dir = "bad"

        if myaddr == dst:
            route_dir = None
        else:
            # Compare nibbles left-to-right
            for i in range(len(myaddr)):

                # We reached this node's left-most zero
                # without any nibble diffs, so dst is a
                # decendant of this node: route down
                if myaddr[i] == 0:
                    route_dir = "down"
                    break

                # Nibble diffs before this node's left-most zero,
                # so dst is on a different branch: route up
                if myaddr[i] != dst[i]:
                    route_dir = "up"
                    break

        assert route_dir != "bad"
        return route_dir


if __name__ == '__main__':
    unittest.main()

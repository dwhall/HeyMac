#!/usr/bin/env python3

"""UDP Bridge AHSM for HeyMac
Routes inbound UDP messages received on a socket to HeyMac
and outbound HeyMac messages to a socket.
"""

import asyncio
import logging

import pq


UDP_PORT = 0xF0B9


class UdpServer:
    def connection_made(self, transport):
        pass

    def datagram_received(self, data, addr):
        UdpRelayAhsm.on_datagram(data, addr)

    def error_received(self, error):
        UdpRelayAhsm.on_error(error)


class UdpBridgeAhsm(pq.Ahsm):

    @pq.Hsm.state
    def initial(me, event):
        pq.Framework.subscribe("DLL_BRIDGE_ERR", me)
        pq.Framework.subscribe("DLL_BRIDGE_RXD", me)
        pq.Signal.register("DLL_BRIDGE_TX")

        loop = asyncio.get_event_loop()
        server = loop.create_datagram_endpoint(UdpServer, local_addr=("localhost", UDP_PORT))
        me.transport, me.protocol = loop.run_until_complete(server)
        return me.tran(me, UdpBridgeAhsm.bridging)


    @pq.Hsm.state
    def bridging(me, event):
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            return me.handled(me, event)

        elif sig == pq.Signal.DLL_BRIDGE_RXD:
            pkt, me.latest_addr = event.value
            # TODO: ack?
            return me.handled(me, event)

        elif sig == pq.Signal.DLL_BRIDGE_ERR:
            logging.error(event.value)
            return me.handled(me, event)

        elif sig == pq.Signal.DLL_BRIDGE_TX:
            pkt = event.value
            # TODO: extract dest addr from pkt (assume port 0xF0B9)
            return me.handled(me, event)

        elif sig == pq.Signal.SIGTERM:
            return me.tran(me, UdpBridgeAhsm.exiting)

        return me.super(me, me.top)


    @pq.Hsm.state
    def exiting(me, event):
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            me.transport.close()
            return me.handled(me, event)
        return me.super(me, me.top)


    # Callbacks interact via messaging
    @staticmethod
    def on_datagram(data, addr):
        e = pq.Event(pq.Signal.DLL_BRIDGE_RXD, (data,addr))
        pq.Framework.publish(e)

    @staticmethod
    def on_error(error):
        e = pq.Event(pq.Signal.DLL_BRIDGE_ERR, (error))
        pq.Framework.publish(e)


if __name__ == "__main__":
    relay = UdpBridgeAhsm(UdpBridgeAhsm.initial)
    relay.start(0)

    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pq.Framework.stop()
    loop.close()

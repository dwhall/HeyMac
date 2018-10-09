#!/usr/bin/env python3

"""An AHSM to bridge HeyMac datagram (UDP) traffic.
Routes inbound UDP messages received to HeyMac
and outbound HeyMac messages to the addressee
both on port 0xF0B9 (61625)
"""

import asyncio
import logging

import farc


UDP_PORT = 0xF0B9


class UdpServer:
    def connection_made(self, transport):
        pass

    def datagram_received(self, data, addr):
        UdpBridgeAhsm.on_datagram(data, addr)

    def error_received(self, error):
        UdpBridgeAhsm.on_error(error)


class UdpBridgeAhsm(farc.Ahsm):

    @farc.Hsm.state
    def initial(me, event):
        farc.Framework.subscribe("DLL_BRIDGE_ERR", me)
        farc.Framework.subscribe("DLL_BRIDGE_IN", me)
        farc.Signal.register("DLL_BRIDGE_OUT")

        loop = asyncio.get_event_loop()
        server = loop.create_datagram_endpoint(UdpServer, local_addr=("localhost", UDP_PORT))
        #me.transport, me.protocol = loop.run_until_complete(server)
        me.transport, _ = loop.run_until_complete(server)
        return me.tran(me, UdpBridgeAhsm.bridging)


    @farc.Hsm.state
    def bridging(me, event):
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return me.handled(me, event)

        elif sig == farc.Signal.DLL_BRIDGE_IN:
            pkt, me.latest_addr = event.value
            # TODO: ack?
            print("bridge in")
            return me.handled(me, event)

        elif sig == farc.Signal.DLL_BRIDGE_ERR:
            logging.error(event.value)
            return me.handled(me, event)

        elif sig == farc.Signal.DLL_BRIDGE_OUT:
            pkt = event.value
            # TODO: extract dest_addr from pkt (assume port 0xF0B9)
            #me.transport.sendto(b"", (dest_addr, UDB_PORT))

            return me.handled(me, event)

        elif sig == farc.Signal.SIGTERM:
            return me.tran(me, UdpBridgeAhsm.exiting)

        return me.super(me, me.top)


    @farc.Hsm.state
    def exiting(me, event):
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            me.transport.close()
            return me.handled(me, event)
        return me.super(me, me.top)


    # Callbacks interact via messaging
    @staticmethod
    def on_datagram(data, addr):
        e = farc.Event(farc.Signal.DLL_BRIDGE_IN, (data,addr))
        farc.Framework.publish(e)

    @staticmethod
    def on_error(error):
        e = farc.Event(farc.Signal.DLL_BRIDGE_ERR, (error))
        farc.Framework.publish(e)


if __name__ == "__main__":
    relay = UdpBridgeAhsm(UdpBridgeAhsm.initial)
    relay.start(0)

    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        farc.Framework.stop()
    loop.close()

from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt

log = core.getLogger()


class Firewall(object):
    """
    A Firewall object is created for each switch that connects.
    A Connection object for that switch is passed to the __init__ function.
    """

    def __init__(self, connection):
        # Keep track of the connection to the switch
        self.connection = connection

        # Bind PacketIn event listener
        connection.addListeners(self)

        # Add switch rules
        # Allow ICMP traffic
        msg_icmp = of.ofp_flow_mod()
        msg_icmp.match = of.ofp_match(
            dl_type=0x0800, nw_proto=1)  # IPv4 and ICMP
        msg_icmp.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        msg_icmp.priority = 100
        self.connection.send(msg_icmp)

        # Allow ARP traffic
        msg_arp = of.ofp_flow_mod()
        msg_arp.match = of.ofp_match(dl_type=0x0806)  # ARP
        msg_arp.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        msg_arp.priority = 100
        self.connection.send(msg_arp)

        # Default drop rule
        msg_drop = of.ofp_flow_mod()
        msg_drop.priority = 50  # Lower priority than ICMP/ARP rules
        self.connection.send(msg_drop)

    def _handle_PacketIn(self, event):
        """
        Packets not handled by switch rules will be
        forwarded here to be handled by the controller.
        """
        packet = event.parsed
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        # Debugging output
        log.info("Unhandled packet: %s", str(packet.dump()))


def launch():
    """
    Starts the component
    """
    def start_switch(event):
        log.debug("Controlling %s", event.connection)
        Firewall(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)

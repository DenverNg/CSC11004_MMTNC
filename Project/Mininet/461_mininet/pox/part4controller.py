# Part 4 of UWCSE's Mininet-SDN project
#
# based on Lab Final from UCSC's Networking Class
# which is based on of_tutorial by James McCauley

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, IPAddr6, EthAddr

log = core.getLogger()

# Convenience mappings of hostnames to ips
IPS = {
    "h10": "10.0.1.10",
    "h20": "10.0.2.20",
    "h30": "10.0.3.30",
    "serv1": "10.0.4.10",
    "hnotrust": "172.16.10.100",
}

# Convenience mappings of hostnames to subnets
SUBNETS = {
    "h10": "10.0.1.0/24",
    "h20": "10.0.2.0/24",
    "h30": "10.0.3.0/24",
    "serv1": "10.0.4.0/24",
    "hnotrust": "172.16.10.0/24",
}


class Part4Controller(object):
    """
    A Connection object for that switch is self.flood()ed to the __init__ function.
    """

    def __init__(self, connection):
        print(connection.dpid)
        # Keep track of the connection to the switch so that we can
        # send it messages!
        self.connection = connection

        # This binds our PacketIn event listener
        connection.addListeners(self)
        # use the dpid to figure out what switch is being created
        if connection.dpid == 1:
            self.s1_setup()
        elif connection.dpid == 2:
            self.s2_setup()
        elif connection.dpid == 3:
            self.s3_setup()
        elif connection.dpid == 21:
            self.cores21_setup()
        elif connection.dpid == 31:
            self.dcs31_setup()
        else:
            print("UNKNOWN SWITCH")
            exit(1)

    def s1_setup(self):
        # put switch 1 rules here
        self.flood()

    def s2_setup(self):
        # put switch 2 rules here
        self.flood()

    def s3_setup(self):
        # put switch 3 rules here
        self.flood()

    def cores21_setup(self):
        # put core switch rules here
        # drop all IP communication from hnotrust to serv1
        msg = of.ofp_flow_mod()
        msg.priority = 1
        msg.match.dl_type = 0x800
        msg.match.nw_src = IPS["hnotrust"]
        msg.match.nw_dst = IPS["serv1"]
        self.connection.send(msg)

        # drop all ICMP from hnotrust
        msg = of.ofp_flow_mod()
        msg.priority = 1
        msg.match.dl_type = 0x800
        msg.match.nw_proto = 1
        msg.match.nw_src = IPS["hnotrust"]
        self.connection.send(msg)

    def dcs31_setup(self):
        # put datacenter switch rules here
        self.flood()

    def flood(self):
        msg = of.ofp_flow_mod()
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        self.connection.send(msg)

    # used in part 4 to handle individual ARP packets
    # not needed for part 3 (USE RULES!)
    # causes the switch to output packet_in on out_port
    def resend_packet(self, packet_in, out_port):
        msg = of.ofp_packet_out()
        msg.data = packet_in
        action = of.ofp_action_output(port=out_port)
        msg.actions.append(action)
        self.connection.send(msg)

    def _handle_PacketIn(self, event):
        """
        Packets not handled by the router rules will be
        forwarded to this method to be handled by the controller
        """
        # Assign an arbitrary MAC address for our controller
        controller_mac = EthAddr('00:00:00:00:00:07')

        packet = event.parsed  # This is the parsed packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        # Check if the packet is an ARP request or reply
        if packet.type == 0x806:  # ARP
            arp_packet = packet.payload

            # Set up a flow rule based on the ARP details. For all IP traffic
            # destined to `arp_packet.protosrc` (the IP address in the ARP request),
            # update the Ethernet destination to `arp_packet.hwsrc` and forward the
            # traffic to the port where the ARP packet was received.
            flow_mod = of.ofp_flow_mod()
            flow_mod.priority = 0
            flow_mod.match.dl_type = 0x800  # IPv4
            flow_mod.match.nw_dst = arp_packet.protosrc
            flow_mod.actions.append(
                of.ofp_action_dl_addr.set_dst(arp_packet.hwsrc))
            flow_mod.actions.append(of.ofp_action_output(port=event.port))
            self.connection.send(flow_mod)

            # Create an ARP reply to respond to the ARP sender, using the controller's
            # MAC address. Swap the source and destination IP/MAC fields to craft the reply.
            arp_packet.opcode = 2  # ARP Reply
            arp_packet.protodst, arp_packet.protosrc = arp_packet.protosrc, arp_packet.protodst
            arp_packet.hwdst = arp_packet.hwsrc
            arp_packet.hwsrc = controller_mac
            packet.dst = packet.src
            packet.src = controller_mac

            # Send the crafted ARP reply back to the port where the request came from.
            self.resend_packet(packet, event.port)


def launch():
    """
    Starts the component
    """

    def start_switch(event):
        log.debug("Controlling %s" % (event.connection,))
        Part4Controller(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)

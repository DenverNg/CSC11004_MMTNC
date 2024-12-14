# Part 3 of UWCSE's Mininet-SDN project
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


class Part3Controller(object):
    """
    A Connection object for that switch is passed to the __init__ function.
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
        self.allow_flood()

    def s2_setup(self):
        # put switch 2 rules here
        self.allow_flood()

    def s3_setup(self):
        # put switch 3 rules here
        self.allow_flood()

    def dcs31_setup(self):
        # put datacenter switch rules here
        self.allow_flood()

    def cores21_setup(self):
        # put core switch rules here
        block

    def allow_flood(self):
        """
        Flood all communications going through the network.
        Drop the rest to avoid hanging iperfs.
        """
        # Allow flood
        self.connection.send(
            of.ofp_flow_mod(action=of.ofp_action_output(port=of.OFPP_FLOOD),
                            priority=2))
        # Drop all other packets
        self.connection.send(of.ofp_flow_mod(priority=1))

    def cores21_setup(self):
        # Define the IP of hnotrust1
        hnotrust_ip = IPS["hnotrust"]

        # Block ICMP traffic from hnotrust1 to h10, h20, h30, and serv1
        for dst in ["h10", "h20", "h30", "serv1"]:
            dst_ip = IPS[dst]
            self.block_icmp_traffic(hnotrust_ip, dst_ip)

        # Block all IP traffic from hnotrust1 to serv1
        self.block_ip_traffic(hnotrust_ip, IPS["serv1"])

        # Allow all other IP traffic
        for src, src_ip in IPS.items():
            for dst, dst_ip in IPS.items():
                if src == "hnotrust" and dst == "serv1":
                    continue  # Skip because it’s already blocked
                elif src == "hnotrust":
                    self.allow_ip_traffic(src_ip, dst_ip)
                elif src != dst:
                    self.allow_ip_traffic(src_ip, dst_ip)

    def block_icmp_traffic(self, src_ip, dst_ip):
        """Block ICMP traffic from src_ip to dst_ip"""
        msg = of.ofp_flow_mod()
        msg.priority = 20  # Higher priority for specific rules
        msg.match.dl_type = 0x0800  # IPv4
        msg.match.nw_proto = 1  # ICMP protocol
        msg.match.nw_src = IPAddr(src_ip)
        msg.match.nw_dst = IPAddr(dst_ip)
        self.connection.send(msg)

    def block_ip_traffic(self, src_ip, dst_ip):
        """Block all IP traffic from src_ip to dst_ip"""
        msg = of.ofp_flow_mod()
        msg.priority = 19  # Slightly lower priority than ICMP rule
        msg.match.dl_type = 0x0800  # IPv4
        msg.match.nw_src = IPAddr(src_ip)
        msg.match.nw_dst = IPAddr(dst_ip)
        self.connection.send(msg)

    def allow_ip_traffic(self, src_ip, dst_ip):
        """Allow all IP traffic from src_ip to dst_ip"""
        msg = of.ofp_flow_mod()
        msg.priority = 10  # Lower priority for default allow rules
        msg.match.dl_type = 0x0800  # IPv4
        msg.match.nw_src = IPAddr(src_ip)
        msg.match.nw_dst = IPAddr(dst_ip)
        msg.actions.append(of.ofp_action_output(port=of.OFPP_NORMAL))
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

        packet = event.parsed  # This is the parsed packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        packet_in = event.ofp  # The actual ofp_packet_in message.
        print(
            "Unhandled packet from " +
            str(self.connection.dpid) + ":" + packet.dump()
        )


def launch():
    """
    Starts the component
    """

    def start_switch(event):
        log.debug("Controlling %s" % (event.connection,))
        Part3Controller(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)

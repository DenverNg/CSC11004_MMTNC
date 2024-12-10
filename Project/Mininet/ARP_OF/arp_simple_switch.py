# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An OpenFlow 1.0 L2 learning switch implementation.
"""


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.lib.packet import arp


class SimpleSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    def add_flow(self, datapath, in_port, dst, actions):
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port, dl_dst=haddr_to_bin(dst))

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)

    def receive_arp (self, datapath, pkt, eth, inPort):
        arpPacket = pkt.get_protocol(arp.arp) # Lay ra thong tin ARP trong goi tin
        
        if arpPacket.opcode ==1:
            arp_srcIp = arpPacket.src_ip #Lay cac field trong goi ARP
            arp_dstIp = arpPacket.dst_ip #Lay cac filed trong goi ARP
            self.logger.info("receive ARP request %s => %s (port %d)" % (eth.src, eth.dst, inPort))
            self.logger.info("Info ARP with IP from %s ask %s" %(arp_srcIp, arp_dstIp))
            self.logger.info("Info ARP with MAC from %s ask %s" %(arpPacket.src_mac, arpPacket.dst_mac))

            self.reply_arp(datapath, eth, arpPacket, inPort) #Goi ham reply_arp
        elif arpPacket.opcode == 2:
            pass

    def reply_arp (self, datapath, eth, arpPacket, inPort):
        dstIP = arpPacket.src_ip
        srcIP = arpPacket.dst_ip
        if srcIP == "10.0.0.2":
            srcMac = "00:00:00:00:00:02"
        elif srcIP == "10.0.0.1":
            srcMac = "00:00:00:00:00:01"
        #create packet arp reply
        e = ethernet.ethernet(dst=arpPacket.src_mac,
                      src=srcMac,
                      ethertype=ether_types.ETH_TYPE_ARP) # Tao goi tin Layer 2
        
        """
        e = ethernet.ethernet(dst='ff:ff:ff:ff:ff:ff',
                      src='08:60:6e:7f:74:e7',
                      ethertype=ether.ETH_TYPE_ARP)
        """
        """
        e = ethernet.ethernet(dst=arpPacket.src_mac,
                      src="ff:ff:ff:ff:ff:ff",
                      ethertype=ether_types.ETH_TYPE_ARP)
        """
        a = arp.arp(hwtype=1, proto=0x0800, hlen=6, plen=4, opcode=2,
            src_mac=srcMac, src_ip=srcIP,
            dst_mac=arpPacket.src_mac, dst_ip=dstIP) # Tao goi tin ARP
        p = packet.Packet() #Tao ra mot Packet
        p.add_protocol(e) #Dua goi tin Layer 2 vao Packet
        p.add_protocol(a) #Dua goi tin ARP vao Packet
        p.serialize()     

        actions = [datapath.ofproto_parser.OFPActionOutput(inPort)] #Dinh nghia action với gói tin PACKET_OUT 
        
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=0xffffffff, in_port=datapath.ofproto.OFPP_CONTROLLER,
            actions=actions, data=p.data) #Dinh nghia goi tin PACKOUT voi action
        datapath.send_msg(out) #Gui thong tin den OF switch
            

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg # Lay ra msg ma OF switch chuyen cho controller thong qua packet_in
        datapath = msg.datapath #Lay ra thong tin OF switch
        ofproto = datapath.ofproto #Trich ra nhung thong tin giao thuc ma OF switch ho tro

        pkt = packet.Packet(msg.data) #Parse goi tin ma OF switch nhan dc tu controller. Trong vi du la goi tin ARP
        eth = pkt.get_protocol(ethernet.ethernet) #Lay ra thong tin layer 2 cua goi tin

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        
        #Phan code them: begin
        if eth.ethertype == ether_types.ETH_TYPE_ARP: #Neu ra goi tin ARP thi xu ly
            self.logger.info("Receive ARP packet")
            inPort = msg.in_port
            self.receive_arp(datapath, pkt, eth, inPort) #Goi ham receive_arp
            return
        else:
            self.logger.info("Drop packet")
            return
        #phan code them: end

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, msg.in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = msg.in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            self.add_flow(datapath, msg.in_port, dst, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
            actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no

        ofproto = msg.datapath.ofproto
        if reason == ofproto.OFPPR_ADD:
            self.logger.info("port added %s", port_no)
        elif reason == ofproto.OFPPR_DELETE:
            self.logger.info("port deleted %s", port_no)
        elif reason == ofproto.OFPPR_MODIFY:
            self.logger.info("port modified %s", port_no)
        else:
            self.logger.info("Illeagal port state %s %s", port_no, reason)

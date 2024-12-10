#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.cli import CLI


class part1_topo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        h1 = self.addHost('h1',mac='00:00:00:00:00:01', ip = '10.0.0.1/24')
        h2 = self.addHost('h2',mac='00:00:00:00:00:02', ip = '10.0.0.2/24')
        h3 = self.addHost('h3',mac='00:00:00:00:00:03', ip = '10.0.0.3/24')
        h4 = self.addHost('h4',mac='00:00:00:00:00:04', ip = '10.0.0.4/24')
        self.addLink(h1,s1)
        self.addLink(h2,s1)
        self.addLink(h3,s1)
        self.addLink(h4,s1)


topos = {"part1": part1_topo}

if __name__ == "__main__":
    t = part1_topo()
    net = Mininet(topo=t)
    net.start()
    CLI(net)
    net.stop()

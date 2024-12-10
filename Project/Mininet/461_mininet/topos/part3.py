#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import RemoteController


class part3_topo(Topo):
    def build(self):
        # add switches
        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")
        s3 = self.addSwitch("s3")
        cores21 = self.addSwitch("cores21")
        dcs31 = self.addSwitch("dcs31")
        # add hosts
        h10 = self.addHost(
            "h10", mac="00:00:00:00:00:01", ip="10.0.1.10/24", defaultRoute="h10-eth0"
        )
        h20 = self.addHost(
            "h20", mac="00:00:00:00:00:02", ip="10.0.2.20/24", defaultRoute="h20-eth0"
        )
        h30 = self.addHost(
            "h30", mac="00:00:00:00:00:03", ip="10.0.3.30/24", defaultRoute="h30-eth0"
        )
        serv1 = self.addHost(
            "serv1",
            mac="00:00:00:00:00:04",
            ip="10.0.4.10/24",
            defaultRoute="serv1-eth0",
        )
        hnotrust1 = self.addHost(
            "hnotrust1",
            mac="00:00:00:00:00:05",
            ip="172.16.10.100/24",
            defaultRoute="hnotrust1-eth0",
        )
        # add links
        self.addLink(h10, s1)
        self.addLink(h20, s2)
        self.addLink(h30, s3)
        self.addLink(s1, cores21)
        self.addLink(s2, cores21)
        self.addLink(s3, cores21)
        self.addLink(serv1, dcs31)
        self.addLink(cores21, dcs31)
        self.addLink(hnotrust1, cores21)


topos = {"part3": part3_topo}


def configure():
    topo = part3_topo()
    net = Mininet(topo=topo, controller=RemoteController)
    net.start()

    # Pre-populate all neighbor tables
    hosts = ["h10", "h20", "h30", "serv1", "hnotrust1"]
    for configuring_host_name in hosts:
        configuring_host = net.get(configuring_host_name)
        for remote_host_name in hosts:
            if configuring_host_name != remote_host_name:
                remote_host = net.get(remote_host_name)
                configuring_host.setARP(remote_host.IP(), remote_host.MAC())

    CLI(net)

    net.stop()


if __name__ == "__main__":
    configure()

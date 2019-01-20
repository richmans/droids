from argparse import ArgumentParser, ArgumentTypeError
from scapy.all import rdpcap, reduce, Scapy_Exception, PacketList
from os.path import isfile
import os
import sys
import logging
from baseline_analyzer import BaselineAnalyzer
from detection_analyzer import DetectionAnalyzer
import re


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


def read_pcap(pcap):
    logging.info("Loading pcap {}".format(pcap))
    if not isfile(pcap):
        logging.error("Could not find pcap file {}".format(pcap))
    try:
        packets = rdpcap(pcap)
    except Scapy_Exception as e:
        logging.error("Could not load pcap {}: {}".format(pcap,str(e)))
        return PacketList()
    logging.debug("Pcap {} succesfuly loaded with {} packets".format(pcap, len(packets)))
    return packets


def read_pcaps(pcap):
    if type(pcap) == list and len(pcap) > 1:
        packets = reduce((lambda l, p: l+p), [read_pcap(p) for p in pcap])
    elif os.path.isdir(pcap[0]):
        packets = reduce((lambda l, p: l+p), [read_pcap(os.path.join(pcap[0],p)) for p in os.listdir(pcap[0])])
    else:
        packets = read_pcap(pcap[0])
    return packets


def error(message):
    logging.error(message)
    sys.exit(1)


def argparse_mac_type(s, pat=r"([a-f0-9A-F]{2}.?){5}[a-f0-9A-F]{2}"):
    reg = re.compile(pat)
    if not reg.match(s):
        raise ArgumentTypeError
    return s.lower()


def main(argv):
    parser = ArgumentParser(description='Process some integers.')
    parser.add_argument('cmd', type=str, choices=['baseline', 'detection'])
    parser.add_argument('pcap',  nargs='+',help='Read a pcap for analysis')
    parser.add_argument('--baseline', type=str, help='baseline .yml file')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--mymac', type=argparse_mac_type, help='Override the mymac detection')
    args = parser.parse_args(argv)
    if args.pcap:
        packets = read_pcaps(args.pcap)
    else:
        error("No pcaps provided")
        
    if args.debug or 'DEBUG' in os.environ:
        logging.getLogger().setLevel(logging.DEBUG)
    if args.cmd == 'baseline':
        analyzer = BaselineAnalyzer()
        baseline = analyzer.run(packets, args.mymac)
        baseline.show()
        baseline.write(args.baseline)
    if args.cmd == 'detection':
        analyzer = DetectionAnalyzer()
        analyzer.load_baseline(args.baseline)
        analyzer.run(packets, args.mymac)
        print(analyzer.render_report())


if __name__ == '__main__':
    main(sys.argv[1:])

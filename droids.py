from argparse import ArgumentParser
from scapy.all import rdpcap, reduce
from os.path import isfile
import sys
import logging
from binascii import hexlify
from baseline_analyzer import BaselineAnalyzer

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')



def read_pcap(pcap):
    logging.info("Loading pcap {}".format(pcap))
    if not isfile(pcap):
        logging.error("Could not find pcap file {}".format(pcap))
    packets = rdpcap(pcap)
    logging.debug("Pcap {} succesfuly loaded with {} packets".format(pcap, len(packets)))
    return packets

def read_pcaps(pcap):
    if type(pcap) == list:
        packets = reduce((lambda l, p: l+p), [read_pcap(p) for p in pcap])
    else:
        packets = read_pcap(pcap)
    return packets

def error(message):
    logging.error(message)
    sys.exit(1)

def main():
    parser = ArgumentParser(description='Process some integers.')
    parser.add_argument('cmd', type=str, choices=['baseline'])
    parser.add_argument('pcap',  nargs='+',help='Read a pcap for analysis')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    if args.cmd == 'baseline':
        packets = read_pcaps(args.pcap)
        analyzer = BaselineAnalyzer()
        baseline = analyzer.create_baseline(packets)
        baseline.show()

if __name__ == '__main__':
    main()

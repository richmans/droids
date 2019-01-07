inetd -f &
tcpdump -i eth0 -w /dumps/trace-%Y-%M-%d_%H.%M.%S.pcap -G 1 -K -n

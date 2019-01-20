# DROIDS
Directly Recognize the Opponent Intrusion Detection System

This is an IDS specificly designed for a Capture-The-Flag event. 

It analyzes tcp and udp conversations to create a baseline of permitted conversations. Then, during the challenge phase, 
it detects conversations that don't fit in the baseline. 
This lets you quickly find the attacks that others are using on your
server.

## Requirements
- Tested only in python3 
- Scapy is used for packet analysis: `pip3 install scapy`
- docker is used only for the demonstration (optional)

## Demonstration
First, let's prepare some pcaps to analyze. The directory droids_demo contains a 
docker instance that runs two services and a tcpdump. The generate_pcaps.sh script invokes those services and
delivers two sets of pcaps:
- a baseline set where the services are invoked normally
- a live set where the services are invoked normally AND are attacked

```
$ cd droids/droids_demo
$ docker build -t droids_demo .
$ ./generate_pcaps.sh
[snip]
Done! Your pcaps are ready in ./example_data !
$ find example_data                                                                                                                              ✔  1791  21:50:22
example_data
example_data/baseline
example_data/baseline/trace-2019-00-07_20.00.26.pcap
example_data/baseline/trace-2019-00-07_20.00.30.pcap
example_data/live
example_data/live/trace-2019-00-07_20.00.56.pcap
example_data/live/trace-2019-00-07_20.00.59.pcap
$
```

The amount of pcaps may vary. No worries, Droids can handle directories of pcaps!
Now that we have some data, let's create a baseline:

```
$ cd ..
$ python3 droids.py baseline --baseline baseline.yml droids_demo/example_data/baseline --mymac 02:42:ad:00:00:11
$ cat baseline.yml 
```

Droids analyzes the pcaps and creates templates of each type of conversation that it finds. These templates are now 
stored in baseline.yml

Now we can use the baseline to detect anomalies in our live data!

```
$ python3 droids.py detection --baseline baseline.yml droids_demo/example_data/live --mymac 02:42:ac:11:00:02
[snip]
[INFO] ==== IDS Anomaly detection ====
[INFO] Read 155 packets in 16 sessions
[WARNING] Conversation on port 80 did not match conversations in the baseline. Best matching score was 0.43
[WARNING] Conversation on port 7 did not match conversations in the baseline. Best matching score was 0.00
$
```

Droids has succesfully identified the two attacks in the live data.

## Service Wrapper
When you find an exploit happening in inetd based service but you have no idea how to patch your executable, 
service_wrapper can be a solution. It sits between inetd and the executable acting as a filter on your stdin and stdout.
Adapt the filter_traffic method to your liking and plug it into your inetd config to stop those incoming attacks! 

## Some notes
The basic idea of this project is: let's diff the packets of each conversation in the baseline to determine which 
part of the conversation is variable. This only works if the data is not encrypted. On encrypted data, the diff will 
simply contain the entire conversation. So: Droids does not work on encrypted traffic like https.

The --mymac parameter defines the macaddress of the host that you are running the IDS for. This is to distinguish 
between incoming and outgoing connections.
Droids can actually detect mymac by counting occurrences of each macaddress. This fails in the demonstration because 
all packets are to or from the docker gateway. 
The --mymac parameter allows you to override the detection in this situation.

The droids_demo contains a very very very simple simulation of a CTF host. It uses inetd to run a http and echo service.
The services on ports 9 and 10 are used for testing the service-wrapper.
It also runs tcpdump to capture all packets. You can inspect the workings of these services in 
`service_cgi.py` and `service_echo.py`. The tcpdump process is started from `service_run.sh`

In an actual event i would setup tcpdump to rotate outputfiles every 60 seconds or so (using the -G parameter) 
and rsync those back to my  private laptop to run Droids locally. This minimizes the amount of installation and setup 
needed on the team server. 
You can install and try out droids on your laptop while preparing for the event.
 
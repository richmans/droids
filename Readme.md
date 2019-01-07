# DROIDS
Directly Recognize the Opponent Intrusion Detection System

This is an IDS specificly designed for a Capture-The-Flag event. It analyzes
tcp and udp conversations to create a baseline of permitted conversations.

Then, during the challenge phase, it detects conversations that don't fit in the
baseline. This lets you quickly find the attacks that others are using on your
server.

## Requirements
- Tested only in python3 
- Scapy is used for packet analysis: `pip3 install scapy`
- docker is used only for the demonstration (optional)

## Demonstration
First, let's prepare some pcaps to analyze. The directory droids_demo contains a 
docker instance that runs two services and a tcpdump. The generate_pcaps.sh script invokes those services and
generates two sets of pcaps:
- a baseline set where the services are invoked normally
- a live set where the services are invoked normally AND are attacked

```
$ cd droids/droids_demo
$ docker build -t droids_demo .
$ ./generate_pcaps.sh
[snip]
Done! Your pcaps are ready in ./example_data !
$
```

Now that we have some data, let's create a baseline:

```
$ cd droids
$ python3 droids.py baseline --baseline baseline.yml droids_demo/example_data/baseline --mymac 0242ad000011
```

Droids analyzes the pcaps and creates templates of each type of conversation that it finds. These templates are now stored in baseline.yml

Now we can use the baseline to detect anomalies in our live data!

```
$ python3 droids.py detection --baseline baseline.yml droids_demo/example_data/live --mymac 0242ac110002
[snip]
[INFO] ==== IDS Anomaly detection ====
[INFO] Read 155 packets in 16 sessions
[WARNING] Conversation on port 80 did not match conversations in the baseline. Best matching score was 0.50
[WARNING] Conversation on port 7 did not match conversations in the baseline. Best matching score was 0.50
$
```

Droids has succesfully identified the two attacks in the live data.
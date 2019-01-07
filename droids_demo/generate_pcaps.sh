echo "Setting up..."
rm -rf /tmp/pcaps
rm -rf ./example_data
mkdir /tmp/pcaps
mkdir ./example_data
mkdir ./example_data/baseline
mkdir ./example_data/live

echo "Starting victim instance"
docker run --mac-address 02:42:ad:00:00:11 --name droids_victim -v /tmp/pcaps:/dumps -p 8881:80 -p 8882:7 -d droids_demo

echo "Running jury requests"
for i in {1..5}
do
  echo 'hallo' | nc localhost 8882
  curl http://localhost:8881/cgi-bin/service_cgi.py?accounting
  curl http://localhost:8881/cgi-bin/service_cgi.py?purchase
done


echo "Restarting droid victim"
docker restart droids_victim
mv /tmp/pcaps/* ./example_data/baseline

echo "Running attack requests"
for i in {1..4}
do
  echo 'hallo' | nc localhost 8882
  curl http://localhost:8881/cgi-bin/service_cgi.py?accounting
done
curl "http://localhost:8881/cgi-bin/service_cgi.py?;cat%20/etc/passwd"
echo 'give-me-flag!' | nc localhost 8882

for i in {1..4}
do
  echo 'hallo' | nc localhost 8882
  curl http://localhost:8881/cgi-bin/service_cgi.py?accounting
done


echo "Killing the victim"
docker stop droids_victim
docker rm -f droids_victim

mv /tmp/pcaps/* ./example_data/live

echo "Done! Your pcaps are ready in ./example_data !"

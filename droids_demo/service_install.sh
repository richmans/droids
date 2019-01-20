echo "echo stream tcp nowait root /service_echo.py" > /etc/inetd.conf
echo "discard stream tcp nowait root /service_wrap.py wrap /service_echo.py" >> /etc/inetd.conf
echo "10 stream tcp nowait root /service_wrap.py wrap cat /etc/services" >> /etc/inetd.conf
echo "http stream tcp nowait root /usr/sbin/httpd httpd -i -c /etc/httpd.conf -h /www" >> /etc/inetd.conf
echo "A:*" > /etc/httpd.conf
mkdir -p /www/cgi-bin
mkdir -p /www/users/accounting/john
mkdir -p /www/users/accounting/alice
mkdir -p /www/users/purchase/bob
mkdir /dumps
mv /service_cgi.py /www/cgi-bin

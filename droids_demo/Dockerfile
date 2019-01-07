FROM alpine
RUN apk update && apk add busybox-extras tcpdump python3 && rm -r /var/cache/
ADD service* /
RUN /service_install.sh
ENTRYPOINT /service_run.sh
EXPOSE 7 80
VOLUME /dumps

FROM forumi0721/alpine-armhf-base:latest

EXPOSE 137/udp 138/udp 139 445

COPY local/. /usr/local/

RUN ["docker-build-start"]

RUN ["docker-init"]

RUN ["docker-build-end"]


COPY smb.conf /conf.d/smb.conf


ENTRYPOINT ["docker-run"]




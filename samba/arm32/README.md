# [alpine-armhf-samba](https://hub.docker.com/r/forumi0721alpinearmhf/alpine-armhf-samba/)
[![](https://images.microbadger.com/badges/version/forumi0721alpinearmhf/alpine-armhf-samba.svg)](https://microbadger.com/images/forumi0721alpinearmhf/alpine-armhf-samba "Get your own version badge on microbadger.com") [![](https://images.microbadger.com/badges/image/forumi0721alpinearmhf/alpine-armhf-samba.svg)](https://microbadger.com/images/forumi0721alpinearmhf/alpine-armhf-samba "Get your own image badge on microbadger.com") [![Docker Stars](https://img.shields.io/docker/stars/forumi0721alpinearmhf/alpine-armhf-samba.svg?style=flat-square)](https://hub.docker.com/r/forumi0721alpinearmhf/alpine-armhf-samba/) [![Docker Pulls](https://img.shields.io/docker/pulls/forumi0721alpinearmhf/alpine-armhf-samba.svg?style=flat-square)](https://hub.docker.com/r/forumi0721alpinearmhf/alpine-armhf-samba/)



----------------------------------------
#### Description
* Distribution : [Alpine Linux](https://alpinelinux.org/)
* Architecture : armhf
* Base Image   : [forumi0721/alpine-armhf-base](https://hub.docker.com/r/forumi0721/alpine-armhf-base/)
* Appplication : [Samba](https://www.samba.org/)
    - Samba is the standard Windows interoperability suite of programs for Linux and Unix.



----------------------------------------
#### Run
```sh
docker run -d -t \
           -p 137:137/udp \
           -p 138:138/udp \
           -p 139:139/tcp \
           -p 445:445/tcp \
           -v /data:/data \
           -e USER_NAME=<username> \
           -e USER_PASSWD=<password> \
           -e USER_UID=<uid> \
           -e USER_GID=<gid> \
           -e NETBIOS_NAME=SAMBA \
           -e WORKGROUP=WORKGROUP \
           -e SAMBA_SHARE="data=/data,..." \
           forumi0721alpinearmhf/alpine-armhf-samba:latest
```



----------------------------------------
#### Usage
* mount share directory
    - Linux : `mount -t cifs -o user=username,pass=passwd //<ip>/data /mnt/data` 
    - Darwin : `mount -t smbfs //username:passwd@<ip>/data /Volumes/data`
    - Default username/password : forumi0721/passwd


###### Notes
* If you want to use multiple user or complex setting, you need to create `smb.conf` and add `-v smb.conf:/conf.d/smb.conf` to docker option.



----------------------------------------
#### Docker Options
| Option             | Description                                      |
|--------------------|--------------------------------------------------|
| -t                 | Allocate a pseudo-TTY                            |


#### Ports
| Port               | Description                                      |
|--------------------|--------------------------------------------------|
| 137/udp            | NetBIOS Name Service                             |
| 138/udp            | NetBIOS Datagram                                 |
| 139/tcp            | NetBIOS Session                                  |
| 445/tcp            | SMB over TCP                                     |


#### Volumes
| Volume             | Description                                      |
|--------------------|--------------------------------------------------|
| /data              | Samba share directory                            |


#### Environment Variables
| ENV                | Description                                      |
|--------------------|--------------------------------------------------|
| USER_NAME          | Login username (default : forumi0721)            |
| USER_PASSWD        | Login password (default : passwd)                |
| USER_EPASSWD       | Login password (base64)                          |
| USER_UID           | Login user uid (default : 1000)                  |
| USER_GID           | Login user gid (default : 100)                   |
| NETBIOS_NAME       | Samba NetBIOS name (default : SAMBA)             |
| WORKGROUP          | Samba workgroup name (default : WORKGROUP)       |
| SAMBA_SHARE        | Samba share directory (default : /data)          |



----------------------------------------
* [forumi0721alpinex64/alpine-x64-samba](https://hub.docker.com/r/forumi0721alpinex64/alpine-x64-samba/)
* [forumi0721alpinearmhf/alpine-armhf-samba](https://hub.docker.com/r/forumi0721alpinearmhf/alpine-armhf-samba/)
* [forumi0721alpineaarch64/alpine-aarch64-samba](https://hub.docker.com/r/forumi0721alpineaarch64/alpine-aarch64-samba/)


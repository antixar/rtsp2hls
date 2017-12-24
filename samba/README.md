# Samba server
[![Docker Pulls](https://img.shields.io/docker/pulls/mashape/kong.svg)](https://hub.docker.com/r/axelhenry/docker-samba-alpine/)

[Samba 4](https://www.samba.org/) server running under [s6 overlay](https://github.com/just-containers/s6-overlay) on [Alpine Linux](https://hub.docker.com/_/alpine/). Runs both `smbd` and `nmbd` services.

## Configuration
See [config directory](/config) for sample config file.

#### smb.conf

To have multiple samba instances running on the host without using port redirection, we'll bind samba to a network interface.
Check if that interface exists or create it (see [host configuration](#host-configuration))

````
bind interfaces only = yes
interfaces = xxx.xxx.xxx.xxx
netbios name = XXXXXXXX
````

#### users.conf

````
#lines beginning with # are comments
#fields are delimited by tabulations
#username	password	uid	gid	groupname
samba	samba	1000	1000	samba
samba_write	write	1001	1000	samba
````

If you want your samba user to be able to write on your share, make sure to give it the same gid as the folder's owner on the host.

## Host Configuration

#### Interface configuration

Examples given are working under debian 8, check your distribution's wiki to adapt files/commands.


/etc/network/interfaces
````
# This file describes the network interfaces avaibable on your system
# and how  to activate them. For more information, see interfaces(5).

#The loopback network interface
auto lo
iface lo inet loopback

#The primary network interface
auto ethX
allow-hotplug ethX
iface ethX inet dhcp

#Loading our vinterface
source /etc/network/interfaces.d/*.vinterface.cfg

````

/etc/network/interfaces.d/smb_givenlabel.vinterface.cfg
````
auto ethX:givenlabel
iface ethX:givenlabel inet static
  address xxx.xxx.xxx.xxx
  netmask xxx.xxx.xxx.xxx
````

Restart your networking service.
````Shell
  service networking restart
````

Ping your newly created interface.

Enjoy.

#### DNS configuration

Right now you can only access to your new interfaces by ip, so if you want to use hostnames, make sure to bind the ip with the desired hostname in your router/dns server/whatever solution you use on your local network.


## Quickstart

Make sure you have [smb.conf](#smbconf) in your config folder. You can specify a username and a password via environment variables, or use defaults values.

````
environment:
  - USERNAME=samba
  - UID=1000
  - GROUPNAME=samba
  - GID=1000
  - PASSWORD=samba
  - S6_VERSION=1.18.1.5
````

````shell
docker run -d --net=host -v /path/to/data:/shared -v /path/to/folder/containing/your/samba/config/file:/config -e USERNAME=user -e PASSWORD=testing --name samba.quickstart axelhenry/docker-samba-alpine
````

## Not so quick start

Make sure you have [smb.conf](#smbconf) and [users.conf](#usersconf) in your config folder.

````shell
docker run -d --net=host -v /path/to/data:/shared -v /path/to/folder/containing/your/configs/files:/config --name samba.nquickstart axelhenry/docker-samba-alpine
````

## Thanks

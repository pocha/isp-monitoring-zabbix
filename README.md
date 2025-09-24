# Linkeye alternative for monitoring ISPs with Zabbix

[Linkeye](linkeye.ai) does monitoring of ISPs by pinging them externally from their server & provide you with alerts & dashboard. At Isha Yoga Center, we have created an inhouse solution of the same using our self hosted [Zabbix](zabbix.com). This repository is for python script that is run externally (on an AWS server) to ping our ISPs on regular basis 

> To post data from outside to Zabbix, the usual way of `zabbix_sender` will not work out. You need to setup a jump server (using ngrok or something similar) to have an external endpoint to which the external script can post data, which will route to zabbix-http & zabbix-http will push the data to zabbix using zabbix_sender


## Setup Instructions

### 1. Zabbix 

Download & install Zabbix on one of your internal machines. Zabbix has SNMP trap support to capture data from switches & other internal devices. You can also choose to install Zabbix agents on switches & other network devices if there is support for that. 

To capture the data sent from the ping script, you need to do the following on the Zabbix UI. 

##### 1.a Create Hosts
For each ISP connection, create a separate host in Zabbix:

- **Groups**: Create/use groups like "ISP Gateways - Primary", "ISP Gateways - Backup"
- **Host name**: Must match `zabbix_hostname` in config.yml (e.g., "ISP-Main-Primary")

##### 1.b Create Items
For each host, create these 3 trapper items:

**Ping**
- **Key**: `ping`
- Name: `Ping Status`
- Type: `Zabbix trapper`
- Type of information: `Numeric (int)`
- Update interval: `0` (trapper)

**Packet Loss Percentage**
- **Key**: `packet_loss`
- Name: `Ping Packet Loss`
- Type: `Zabbix trapper`
- Type of information: `Numeric (float)`
- Units: `%`
- Update interval: `0` (trapper)

**Average Round Trip Time**
- **Key**: `avg_time`
- Name: `Ping Average RTT`
- Type: `Zabbix trapper`
- Type of information: `Numeric (float)`
- Units: `ms`
- Update interval: `0` (trapper)

### 2. Setup `zabbix-sender-http` on machine running zabbix

Download & install [zabbix-sender-http](https://github.com/0xdeface/zabbix-sender-http). Links to install the binary are on the README of the zabbix-sender-http project. It has to be installed on the same machine where Zabbix is running. 

Start zabbix-sender-http on port 8081 (Our zabbix is running on port 8080, so we chose to run zabbix-sender-http on 8081. You can choose any port of your choice)

```
Command -> ./zabbix-http -http-port 8081

 zabbix server addr: 127.0.0.1:10051 
 http server port: 8081 

```

### 3. Setup `tailscale` tunnel/funnel on machine running Zabbix

We chose tailscale instead of `ngrok`. Reason being, tailscale allows for a specific custom tailscale domain everytime we created a tunnel, in their free tier as well. ngrok will create a new url everytime we create a tunnel in its free tier. We recommend using tailscale for this reason

Install instruction (for linux machine) 

```
curl -fsSL https://tailscale.com/install.sh | sh   
```

Create Tunnel to port 8081 on which zabbix-sender-http is listening 

```
Command -> sudo tailscale funnel --bg 8081

[sudo] password for isha: 
Available on the internet:

https://ifiycitsklt395.tail386825.ts.net/
|-- proxy http://127.0.0.1:8081

Funnel started and running in the background.
To disable the proxy, run: tailscale funnel --https=443 off
```

With the above steps, a tunnel is now created from xxx.ts.net -> zabbix-sender-http, as it is running on 8081 

Note the url **https://ifiycitsklt395.tail386825.ts.net/** which you should be passing as Env variable `ZABBIX_SERVER` to the script. This is the url to which the ping script will send data to. 


### 4. Clone this repository on ping server & do the following: 

#### 4.a Edit config file 

Edit `config.yml` to add your ISP gateway locations. Each location can have multiple ISPs. Sample config file below. 

```yaml
locations:
  iyc:
    description: "Main office with dual ISP setup"
    isps:
      primary:
        http_ip: "192.168.1.1"
        zabbix_hostname: "ISP-Main-Primary"
      backup:
        http_ip: "192.168.1.254"
        zabbix_hostname: "ISP-Main-Backup"
  ssb:
    description: "Sadhguru Sannidhi"
    isps:
      primary:
        http_ip: "192.168.1.1"
        zabbix_hostname: "SSB-Main-Primary"
      backup:
        http_ip: "192.168.1.254"
        zabbix_hostname: "SSB-Main-Backup"

```



#### 4.b Run the script
```
ZABBIX_SERVER=<ip of tailscale server> python3 ping_monitor.py
```

**Sample Log Output**

```
2024-01-15 10:00:01 - INFO - Starting ping monitor - Zabbix server: zabbix.company.com:10051
2024-01-15 10:00:01 - INFO - Processing location: main_office
2024-01-15 10:00:01 - INFO -   Monitoring ISP: Comcast Business (Primary) - 192.168.1.1
2024-01-15 10:00:02 - INFO -     OK - Loss: 0.0%, Avg RTT: 15.2ms
2024-01-15 10:00:02 - INFO -   Monitoring ISP: Verizon Business (Backup) - 192.168.1.254
2024-01-15 10:00:03 - INFO -     OK - Loss: 0.0%, Avg RTT: 22.8ms
2024-01-15 10:00:03 - INFO - Processing location: branch_office
2024-01-15 10:00:03 - INFO -   Monitoring ISP: AT&T Business (Primary) - 192.168.2.1
2024-01-15 10:00:04 - INFO -     OK - Loss: 2.0%, Avg RTT: 45.1ms
2024-01-15 10:00:04 - INFO - Monitoring complete - Locations: 4, ISPs: 8
2024-01-15 10:00:04 - INFO - Zabbix metrics - Success: 32, Failed: 0
```

#### (optional) 4.c Setting up as service on Ubuntu machine

If you want the script to run automatically on server start/reboot, do the following steps. 

**Note, these steps are for an Ubuntu machine.**

- Check & update values in ping_monitor.service. Specifically the path to ping_monitor.py & tailscale url with your jump server location. 
- Copy the file to `/etc/systemd/system` as root
- Execute `sudo systemctl reload-daemon` for the new service to be registered
- Start the service with `sudo systemctl start ping_monitor`
- Check logs in syslog `tail -f /var/log/syslog`


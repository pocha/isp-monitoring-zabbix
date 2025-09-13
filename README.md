# ISP Gateway Ping Monitor - Multi-ISP Support

This GitHub Actions workflow monitors multiple ISP gateway connections per location by pinging gateway IPs every 5 minutes and sending metrics to Zabbix. Perfect for monitoring redundant ISP setups with primary, backup, and cellular connections.

## Features

- **Multi-ISP per Location**: Monitor primary, backup, cellular, and multiple fiber connections
- **Automated Monitoring**: Runs every 5 minutes via GitHub Actions
- **Zabbix Integration**: Sends metrics using ~~zabbix_sender~~ [zabbix-sender-http](https://github.com/0xdeface/zabbix-sender-http)

## Setup Instructions

### Setup `zabbix-sender-http`
Download & install [zabbix-sender-http](https://github.com/0xdeface/zabbix-sender-http). Links to install are on the README of the project. It has to be installed on the same machine where Zabbix is running. 

Start zabbix-sender-http on port 8081 (Zabbix is running on port 8080)

```
Command -> ./zabbix-http -http-port 8081

 zabbix server addr: 127.0.0.1:10051 
 http server port: 8081 

```

### Setup `tailscale` tunnel/funnel

Install

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

Note the url **https://ifiycitsklt395.tail386825.ts.net/** which is required in the next step. 

### Setup Repository Secrets
Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

- `ZABBIX_SERVER`: ~~Your Zabbix server hostname/IP (e.g., `example.com`)~~ Tailscale server address (with https://)
- `ZABBIX_PORT`: ~~Zabbix trapper port (default: `10051`)~~ Set to Port 80

### Setup Configuration
Edit `config.yml` to add your ISP gateway locations. Each location can have multiple ISPs:

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

### Zabbix Server Configuration

#### Create Hosts
For each ISP connection, create a separate host in Zabbix:

- **Groups**: Create/use groups like "ISP Gateways - Primary", "ISP Gateways - Backup"
- **Host name**: Must match `zabbix_hostname` in config.yml (e.g., "ISP-Main-Primary")
- **Visible name**: Descriptive name (e.g., "Main Office - Comcast Primary")

#### Create Items
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


## Manual Execution

Test locally before deploying:

### Check if ISP's http ip are pingable
- If not pingable, replace them with some local ip in `config.yml`

### Check `zabbix-sender-http` is running 
- Follow steps in setup to install zabbix-sender-http. 
- **zabbix-sender-http need to be installed on the same machine where zabbix is running**
- launch zabbix-sender-http as `./zabbix-http -http-port 8081`

### Install python & dependencies
- Download python from [https://www.python.org/downloads/](https://www.python.org/downloads/) & follow instructions to install
- Run `pip install pyyaml` to install dependency

### Install tcping
- `sudo dpkg -i tcping.deb`

### Run the script
```
ZABBIX_SERVER=<ip of server running zabbix> ZABBIX_PORT=8081  python3 ping_monitor.py
```

## Sample Log Output

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


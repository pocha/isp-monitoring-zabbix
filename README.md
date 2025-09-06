# ISP Gateway Ping Monitor - Multi-ISP Support

This GitHub Actions workflow monitors multiple ISP gateway connections per location by pinging gateway IPs every 5 minutes and sending metrics to Zabbix. Perfect for monitoring redundant ISP setups with primary, backup, and cellular connections.

## Features

- **Multi-ISP per Location**: Monitor primary, backup, cellular, and multiple fiber connections
- **Automated Monitoring**: Runs every 5 minutes via GitHub Actions
- **Zabbix Integration**: Sends metrics using zabbix_sender
- **Comprehensive Logging**: Detailed logs with execution artifacts
- **Flexible Configuration**: YAML-based configuration for easy management

## Setup Instructions

### 1. Repository Secrets
Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

- `ZABBIX_SERVER`: Your Zabbix server hostname/IP (e.g., `example.com`)
- `ZABBIX_PORT`: Zabbix trapper port (default: `10051`)

### 2. Configuration
Edit `config.yml` to add your ISP gateway locations. Each location can have multiple ISPs:

```yaml
locations:
  main_office:
    description: "Main office with dual ISP setup"
    isps:
      primary:
        gateway_ip: "192.168.1.1"
        zabbix_hostname: "ISP-Main-Primary"
        isp_name: "Comcast Business"
        connection_type: "Primary"
      backup:
        gateway_ip: "192.168.1.254"
        zabbix_hostname: "ISP-Main-Backup"
        isp_name: "Verizon Business"
        connection_type: "Backup"
```

### 3. Zabbix Server Configuration

#### Create Hosts
For each ISP connection, create a separate host in Zabbix:

- **Host name**: Must match `zabbix_hostname` in config.yml (e.g., "ISP-Main-Primary")
- **Visible name**: Descriptive name (e.g., "Main Office - Comcast Primary")
- **Groups**: Create/use groups like "ISP Gateways - Primary", "ISP Gateways - Backup"
- **Interfaces**: Add Agent interface (IP can be 127.0.0.1 since we use trapper items)

#### Create Items
For each host, create these 4 trapper items:

**1. Packet Loss Percentage**
- **Name**: `Ping Packet Loss`
- **Type**: `Zabbix trapper`
- **Key**: `ping.loss`
- **Type of information**: `Numeric (float)`
- **Units**: `%`
- **Update interval**: `0` (trapper)

**2. Average Round Trip Time**
- **Name**: `Ping Average RTT`
- **Type**: `Zabbix trapper`
- **Key**: `ping.avg`
- **Type of information**: `Numeric (float)`
- **Units**: `ms`
- **Update interval**: `0` (trapper)

**3. Minimum Round Trip Time**
- **Name**: `Ping Minimum RTT`
- **Type**: `Zabbix trapper`
- **Key**: `ping.min`
- **Type of information**: `Numeric (float)`
- **Units**: `ms`
- **Update interval**: `0` (trapper)

**4. Maximum Round Trip Time**
- **Name**: `Ping Maximum RTT`
- **Type**: `Zabbix trapper`
- **Key**: `ping.max`
- **Type of information**: `Numeric (float)`
- **Units**: `ms`
- **Update interval**: `0` (trapper)

#### Suggested Triggers

**Primary ISP Down (Disaster)**
```
Expression: last(/ISP-Main-Primary/ping.loss)=100
Severity: Disaster
Description: Primary ISP {HOST.NAME} is completely unreachable
```

**Backup ISP Down (High)**
```
Expression: last(/ISP-Main-Backup/ping.loss)=100
Severity: High
Description: Backup ISP {HOST.NAME} is unreachable
```

**High Packet Loss on Primary (High)**
```
Expression: last(/ISP-Main-Primary/ping.loss)>10
Severity: High
Description: High packet loss ({ITEM.LASTVALUE}%) on primary ISP {HOST.NAME}
```

**High Packet Loss on Backup (Warning)**
```
Expression: last(/ISP-Main-Backup/ping.loss)>10
Severity: Warning
Description: High packet loss ({ITEM.LASTVALUE}%) on backup ISP {HOST.NAME}
```

**High Latency (Warning)**
```
Expression: last(/ISP-Main-Primary/ping.avg)>100
Severity: Warning
Description: High latency ({ITEM.LASTVALUE}ms) on {HOST.NAME}
```

#### Suggested Graphs and Dashboards

**Per-Location ISP Comparison**
- Create graphs comparing all ISPs at each location
- Include packet loss and RTT metrics side by side

**ISP Redundancy Dashboard**
- Overview of all primary vs backup connections
- Status indicators for each location's connectivity

**Network Quality Trends**
- Historical view of packet loss and latency
- Identify patterns and degradation over time

## Configuration Examples

### Dual ISP Setup (Most Common)
```yaml
office_location:
  description: "Office with primary and backup ISP"
  isps:
    primary:
      gateway_ip: "192.168.1.1"
      zabbix_hostname: "ISP-Office-Primary"
      isp_name: "Comcast Business"
      connection_type: "Primary"
    backup:
      gateway_ip: "192.168.1.254"
      zabbix_hostname: "ISP-Office-Backup"
      isp_name: "Verizon Business"
      connection_type: "Backup"
```

### Triple ISP Setup (High Availability)
```yaml
datacenter:
  description: "Data center with dual fiber + cellular backup"
  isps:
    fiber_a:
      gateway_ip: "10.0.1.1"
      zabbix_hostname: "ISP-DC-FiberA"
      isp_name: "Level3"
      connection_type: "Fiber A"
    fiber_b:
      gateway_ip: "10.0.2.1"
      zabbix_hostname: "ISP-DC-FiberB"
      isp_name: "Cogent"
      connection_type: "Fiber B"
    cellular:
      gateway_ip: "10.0.100.1"
      zabbix_hostname: "ISP-DC-Cellular"
      isp_name: "Verizon Wireless"
      connection_type: "Cellular Backup"
```

## How It Works

1. **Schedule**: GitHub Actions runs every 5 minutes via cron
2. **Configuration**: Loads ISP gateway details from config.yml
3. **Multi-ISP Processing**: Iterates through each location and all ISPs
4. **Ping Testing**: Sends 5 ping packets to each gateway IP
5. **Statistics**: Extracts packet loss % and RTT (min/avg/max)
6. **Zabbix Integration**: Uses zabbix_sender to push metrics
7. **Logging**: Creates detailed logs with per-ISP results

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

## Manual Execution

Test locally before deploying:

```bash
# Install dependencies
sudo apt-get install zabbix-sender iputils-ping
pip install pyyaml

# Set environment variables
export ZABBIX_SERVER="your-zabbix-server.com"
export ZABBIX_PORT="10051"

# Run the script
python ping_monitor.py
```

## Troubleshooting

### Common Issues

**Configuration Errors**
- Verify YAML syntax in config.yml
- Ensure all required fields are present for each ISP
- Check that zabbix_hostname values are unique

**Connectivity Issues**
- Test Zabbix server connectivity: `telnet your-server 10051`
- Verify gateway IPs are reachable: `ping gateway-ip`
- Check GitHub Actions runner can reach your Zabbix server

**Zabbix Integration**
- Ensure hostnames in config.yml exactly match Zabbix host names
- Verify trapper items are configured correctly
- Test zabbix_sender manually:
  ```bash
  zabbix_sender -z server -p 10051 -s ISP-Main-Primary -k ping.loss -o 0
  ```

### Finding Gateway IPs

**Windows**
```cmd
ipconfig /all
# Look for "Default Gateway" entries
```

**Linux/Mac**
```bash
ip route show | grep default
# or
route -n | grep UG
```

**Router Configuration**
- Access router admin panel (usually 192.168.1.1 or 192.168.0.1)
- Look for WAN or Internet connection settings
- Each ISP connection will have its own gateway

## Files Structure

```
isp-monitoring-zabbix/
├── .github/workflows/
│   └── ping-monitor.yml     # GitHub Actions workflow
├── ping_monitor.py          # Main monitoring script
├── config.yml              # Multi-ISP configuration
└── README.md               # This documentation
```

## Advanced Configuration

### Custom Ping Parameters
Modify the script to adjust ping behavior:
- Change ping count (default: 5 packets)
- Adjust timeout values (default: 3 seconds)
- Modify ping interval

### Additional Metrics
The script can be extended to include:
- Jitter calculations
- Packet size variations
- IPv6 support
- Custom Zabbix item keys

### Alerting Integration
Combine with Zabbix alerting for:
- Email notifications on ISP failures
- SMS alerts for critical outages
- Slack/Teams integration
- Automated failover triggers

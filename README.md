# ISP Gateway Ping Monitor

This GitHub Actions workflow monitors ISP gateway connectivity by pinging gateway IPs every 5 minutes and sending metrics to Zabbix.

## Setup Instructions

### 1. Repository Secrets
Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

- `ZABBIX_SERVER`: Your Zabbix server hostname/IP (e.g., `example.com`)
- `ZABBIX_PORT`: Zabbix trapper port (default: `10051`)

### 2. Configuration
Edit `config.yml` to add your ISP gateway locations:

```yaml
locations:
  location_name:
    gateway_ip: "192.168.1.1"          # Your ISP gateway IP
    zabbix_hostname: "ISP-Gateway-Main" # Must match Zabbix host
```

### 3. Zabbix Server Configuration

#### Create Hosts
For each location, create a host in Zabbix with:
- **Host name**: Must match `zabbix_hostname` in config.yml
- **Visible name**: Descriptive name (e.g., "Main Office ISP Gateway")
- **Groups**: Create/use group like "ISP Gateways"
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
Create triggers for monitoring:

**High Packet Loss**
```
Expression: last(/ISP-Gateway-Main/ping.loss)>10
Severity: High
Description: Packet loss is above 10% on {HOST.NAME}
```

**Gateway Unreachable**
```
Expression: last(/ISP-Gateway-Main/ping.loss)=100
Severity: Disaster
Description: Gateway {HOST.NAME} is completely unreachable
```

**High Latency**
```
Expression: last(/ISP-Gateway-Main/ping.avg)>100
Severity: Warning
Description: Average ping time is above 100ms on {HOST.NAME}
```

#### Suggested Graphs
Create graphs to visualize:
1. **Packet Loss Over Time** - ping.loss
2. **Round Trip Times** - ping.min, ping.avg, ping.max
3. **Network Quality Dashboard** - Combined view of all metrics

## How It Works

1. **Schedule**: Runs every 5 minutes via GitHub Actions cron
2. **Ping**: Sends 5 ping packets to each gateway IP
3. **Parse**: Extracts packet loss % and RTT statistics
4. **Send**: Uses `zabbix_sender` to push metrics to Zabbix server
5. **Log**: Creates artifacts with execution logs

## Manual Execution

You can manually trigger the workflow from the Actions tab in GitHub, or run locally:

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

- Check GitHub Actions logs for execution details
- Verify Zabbix server connectivity: `telnet your-server 10051`
- Test zabbix_sender manually: `zabbix_sender -z server -p 10051 -s hostname -k ping.loss -o 0`
- Ensure hostnames in config.yml exactly match Zabbix host names
- Check that Zabbix server accepts data from GitHub Actions IP ranges

## Files

- `.github/workflows/ping-monitor.yml` - GitHub Actions workflow
- `ping_monitor.py` - Main monitoring script
- `config.yml` - Gateway configuration
- `ping_monitor.log` - Execution logs (artifact)

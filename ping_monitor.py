#!/usr/bin/env python3
import os
import yaml
import subprocess
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ping_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_file='config.yml'):
    """Load configuration from YAML file"""
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config file {config_file}: {e}")
        sys.exit(1)

def ping_gateway(ip_address, count=5):
    """Ping gateway and return statistics"""
    try:
        cmd = ['ping', '-c', str(count), '-W', '3', ip_address]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Parse ping output for statistics
            lines = result.stdout.split('\n')
            stats_line = None
            
            for line in lines:
                if 'packet loss' in line:
                    # Extract packet loss percentage
                    loss_percent = line.split('%')[0].split()[-1]
                    packet_loss = float(loss_percent)
                elif 'min/avg/max' in line or 'rtt min/avg/max' in line:
                    # Extract round trip times
                    stats_line = line
            
            if stats_line:
                # Parse: rtt min/avg/max/mdev = 1.234/5.678/9.012/1.234 ms
                times = stats_line.split('=')[1].strip().split('/')[0:3]
                min_time = float(times[0])
                avg_time = float(times[1])
                max_time = float(times[2])
                
                return {
                    'success': True,
                    'packet_loss': packet_loss,
                    'min_time': min_time,
                    'avg_time': avg_time,
                    'max_time': max_time
                }
            else:
                return {
                    'success': True,
                    'packet_loss': packet_loss,
                    'avg_time': 0,
                    'min_time': 0,
                    'max_time': 0
                }
        else:
            # Ping failed completely
            return {
                'success': False,
                'packet_loss': 100.0,
                'avg_time': 0,
                'min_time': 0,
                'max_time': 0
            }
            
    except Exception as e:
        logger.error(f"Error pinging {ip_address}: {e}")
        return {
            'success': False,
            'packet_loss': 100.0,
            'avg_time': 0,
            'min_time': 0,
            'max_time': 0
        }

def send_to_zabbix(zabbix_server, zabbix_port, hostname, key, value):
    """Send data to Zabbix using zabbix_sender"""
    try:
        cmd = [
            'zabbix_sender',
            '-z', zabbix_server,
            '-p', str(zabbix_port),
            '-s', hostname,
            '-k', key,
            '-o', str(value)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            logger.info(f"Successfully sent {key}={value} for {hostname}")
            return True
        else:
            logger.error(f"Failed to send to Zabbix: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending to Zabbix: {e}")
        return False

def main():
    # Get Zabbix server details from environment or use defaults
    zabbix_server = os.getenv('ZABBIX_SERVER', 'example.com')
    zabbix_port = int(os.getenv('ZABBIX_PORT', '10051'))
    
    logger.info(f"Starting ping monitor - Zabbix server: {zabbix_server}:{zabbix_port}")
    
    # Load configuration
    config = load_config()
    
    if 'locations' not in config:
        logger.error("No 'locations' found in config file")
        sys.exit(1)
    
    total_success = 0
    total_failed = 0
    total_isps = 0
    
    # Process each location
    for location_name, location_data in config['locations'].items():
        logger.info(f"Processing location: {location_name}")
        
        if 'isps' not in location_data:
            logger.error(f"No 'isps' found for location {location_name}")
            continue
        
        # Process each ISP at this location
        for isp_id, isp_data in location_data['isps'].items():
            total_isps += 1
            gateway_ip = isp_data.get('gateway_ip')
            zabbix_hostname = isp_data.get('zabbix_hostname')
            isp_name = isp_data.get('isp_name', 'Unknown ISP')
            connection_type = isp_data.get('connection_type', 'Unknown')
            
            if not gateway_ip or not zabbix_hostname:
                logger.error(f"Missing gateway_ip or zabbix_hostname for {location_name}/{isp_id}")
                continue
            
            logger.info(f"  Monitoring ISP: {isp_name} ({connection_type}) - {gateway_ip}")
            
            # Ping the gateway
            ping_result = ping_gateway(gateway_ip)
            
            # Send metrics to Zabbix
            metrics = [
                ('ping.loss', ping_result['packet_loss']),
                ('ping.avg', ping_result['avg_time']),
                ('ping.min', ping_result['min_time']),
                ('ping.max', ping_result['max_time'])
            ]
            
            for key, value in metrics:
                success = send_to_zabbix(zabbix_server, zabbix_port, zabbix_hostname, key, value)
                if success:
                    total_success += 1
                else:
                    total_failed += 1
            
            # Log results for this ISP
            status = "OK" if ping_result['packet_loss'] < 100 else "FAILED"
            logger.info(f"    {status} - Loss: {ping_result['packet_loss']}%, Avg RTT: {ping_result['avg_time']}ms")
    
    logger.info(f"Monitoring complete - Locations: {len(config['locations'])}, ISPs: {total_isps}")
    logger.info(f"Zabbix metrics - Success: {total_success}, Failed: {total_failed}")
    
    if total_failed > 0:
        logger.warning(f"Some metrics failed to send to Zabbix ({total_failed} failures)")
        sys.exit(1)

if __name__ == "__main__":
    main()

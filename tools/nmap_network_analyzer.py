import streamlit as st

try:
    import nmap
except ImportError:
    nmap = None

import socket
import ipaddress
import subprocess
import re
import requests

def get_all_networks():
    networks = []
    try:
        import psutil
        addrs = psutil.net_if_addrs()
        # Try to get gateways if netifaces is available
        gateways = {}
        try:
            import netifaces
            gws = netifaces.gateways()
            for iface in addrs:
                gw = None
                if 'default' in gws and netifaces.AF_INET in gws['default']:
                    gw = gws['default'][netifaces.AF_INET][0]
                gateways[iface] = gw
        except ImportError:
            pass
        for iface, addr_list in addrs.items():
            for addr in addr_list:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    networks.append({
                        'iface': iface,
                        'ip': addr.address,
                        'netmask': addr.netmask,
                        'gateway': gateways.get(iface, "Unknown")
                    })
    except ImportError:
        # Fallback: just get IP using socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            networks.append({'iface': 'default', 'ip': ip, 'netmask': 'Unknown', 'gateway': 'Unknown'})
        except Exception:
            pass
    return networks

def get_cidr_from_ip_netmask(ip, netmask):
    try:
        if ip != "Unknown" and netmask != "Unknown":
            network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
            return str(network)
    except Exception:
        pass
    return "192.168.1.0/24"

def run_arp_scan():
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True, check=True)
        output = result.stdout
        entries = []
        lines = output.splitlines()
        for line in lines:
            match = re.match(r"\s*([0-9.]+)\s+([a-fA-F0-9:-]+)\s+(dynamic|static)", line)
            if match:
                entries.append({
                    "IP": match.group(1),
                    "MAC": match.group(2).replace('-', ':').lower(),
                    "Type": match.group(3)
                })
        return entries
    except Exception as e:
        return []

def lookup_mac_vendor(mac):
    # Use macvendors.co API (free, public, but rate-limited)
    try:
        oui = mac.upper().replace(':', '').replace('-', '')[:6]
        url = f'https://api.macvendors.com/{mac}'
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            return resp.text
        else:
            return 'Unknown'
    except Exception:
        return 'Unknown'

def get_arp_by_ip(arp_entries):
    return {entry['IP']: entry for entry in arp_entries} if arp_entries else {}

def render():
    # Gather all networks
    if 'all_networks' not in st.session_state:
        st.session_state['all_networks'] = get_all_networks()
    networks = st.session_state['all_networks']

    # Show all networks in a table
    if networks:
        st.subheader("Available Network Interfaces")
        import pandas as pd
        st.dataframe(pd.DataFrame(networks))
        # Let user pick which network to use
        iface_labels = [f"{n['iface']} ({n['ip']}/{n['netmask']})" for n in networks]
        default_iface_idx = 0
        selected_iface_idx = st.selectbox("Select network/interface for scan target", range(len(networks)), format_func=lambda i: iface_labels[i], index=default_iface_idx)
        selected_network = networks[selected_iface_idx]
        ip = selected_network['ip']
        netmask = selected_network['netmask']
        gateway = selected_network['gateway']
    else:
        ip = "Unknown"
        netmask = "Unknown"
        gateway = "Unknown"

    if st.button("Refresh Network Info", key="refresh_netinfo"):
        st.session_state['all_networks'] = get_all_networks()
        networks = st.session_state['all_networks']
        if networks:
            selected_network = networks[0]
            ip = selected_network['ip']
            netmask = selected_network['netmask']
            gateway = selected_network['gateway']
        else:
            ip = netmask = gateway = "Unknown"

    st.info(f"**Selected interface:** {ip}\n\n**Gateway:** {gateway}\n\n**Netmask:** {netmask}")

    # Always run ARP scan before displaying hosts
    arp_entries = run_arp_scan()
    arp_by_ip = get_arp_by_ip(arp_entries)

    # Optionally show ARP table for reference (comment out if not needed)
    # if arp_entries:
    #     import pandas as pd
    #     st.subheader("ARP Table (Local Network)")
    #     st.dataframe(pd.DataFrame(arp_entries))

    # Compute default CIDR
    default_cidr = get_cidr_from_ip_netmask(ip, netmask)

    if nmap is None:
        st.error("The python-nmap package is required. Please install it with 'pip install python-nmap'.")
        return

    # Check if nmap is installed on the system
    import shutil
    if not shutil.which("nmap"):
        st.error("nmap is not installed or not found in PATH. Please install nmap from https://nmap.org/download.html.")
        return

    # Session state for scan results
    if 'nmap_scan_results' not in st.session_state:
        st.session_state['nmap_scan_results'] = None
    if 'nmap_scan_hosts' not in st.session_state:
        st.session_state['nmap_scan_hosts'] = []

    target = st.text_input("Target network or host (CIDR or IP)", value=default_cidr)
    scan_type = st.selectbox("Scan type", ["Quick (top ports)", "Full (all ports)"])
    scan_btn = st.button("Start Scan", type="primary")

    if scan_btn and target:
        st.info(f"Scanning {target}... This may take a while.")
        nm = nmap.PortScanner()
        try:
            if scan_type == "Quick (top ports)":
                args = "-T4 --top-ports 20"
            else:
                args = "-T4 -p 1-1024"
            with st.spinner("Running nmap scan..."):
                scan_result = nm.scan(hosts=target, arguments=args)
            hosts = nm.all_hosts()
            st.session_state['nmap_scan_results'] = scan_result
            st.session_state['nmap_scan_hosts'] = hosts
            if not hosts:
                st.warning("No hosts found.")
                return
        except Exception as e:
            st.error(f"Error running nmap scan: {e}")
            return

    # Display nmap results with ARP info in expanders
    scan_result = st.session_state.get('nmap_scan_results')
    hosts = st.session_state.get('nmap_scan_hosts', [])
    # Union of all hosts from nmap and ARP
    arp_ips = set(arp_by_ip.keys())
    nmap_ips = set(hosts)
    all_ips = sorted(arp_ips | nmap_ips, key=lambda ip: tuple(int(x) for x in ip.split('.')) if ip.count('.') == 3 else ip)

    # --- Summary Section ---
    if scan_result and hosts:
        import pandas as pd
        # Machine summary
        machine_rows = []
        for host in hosts:
            nmhost = scan_result['scan'][host]
            arp = arp_by_ip.get(host, {})
            mac = arp.get('MAC', 'Unknown')
            vendor = lookup_mac_vendor(mac) if mac != 'Unknown' else 'Unknown'
            state = nmhost.get('status',{}).get('state','unknown')
            machine_rows.append({
                'IP': host,
                'MAC': mac,
                'Vendor': vendor,
                'State': state
            })
        st.subheader("Machines Found (nmap)")
        st.dataframe(pd.DataFrame(machine_rows))

        # Open ports summary
        port_map = {}
        for host in hosts:
            nmhost = scan_result['scan'][host]
            if 'tcp' in nmhost:
                for port, portdata in nmhost['tcp'].items():
                    if portdata.get('state') == 'open':
                        key = (port, portdata.get('name', ''))
                        if key not in port_map:
                            port_map[key] = []
                        port_map[key].append(host)
        port_rows = []
        for (port, service), iplist in sorted(port_map.items()):
            port_rows.append({
                'Port': port,
                'Service': service,
                'Open On': ', '.join(iplist)
            })
        st.subheader("Open Ports Summary")
        st.dataframe(pd.DataFrame(port_rows))

    # --- Per-host details ---
    if scan_result and all_ips:
        st.subheader("Discovered Hosts and Open Ports")
        import pandas as pd
        for host in all_ips:
            nmhost = scan_result['scan'][host] if scan_result and 'scan' in scan_result and host in scan_result['scan'] else None
            arp = arp_by_ip.get(host, {})
            mac = arp.get('MAC', 'Unknown')
            mac_type = arp.get('Type', 'Unknown')
            vendor = lookup_mac_vendor(mac) if mac != 'Unknown' else 'Unknown'
            expander_label = f"Host: {host} (MAC: {mac}, Type: {mac_type}, Vendor: {vendor})"
            with st.expander(expander_label, expanded=False):
                st.write(f"**IP:** {host}")
                st.write(f"**MAC:** {mac}")
                st.write(f"**Vendor:** {vendor}")
                st.write(f"**ARP Type:** {mac_type}")
                if nmhost:
                    st.write(f"**State:** {nmhost.get('status',{}).get('state','unknown')}")
                    if 'tcp' in nmhost:
                        ports = nmhost['tcp']
                        if ports:
                            df = []
                            for port, portdata in ports.items():
                                state = portdata.get('state', '')
                                icon = '🟢' if state == 'open' else '🔴'
                                df.append({
                                    'Port': port,
                                    'State': f"{icon} {state}",
                                    'Service': portdata.get('name', ''),
                                    'Product': portdata.get('product', ''),
                                    'Version': portdata.get('version', ''),
                                })
                            st.dataframe(pd.DataFrame(df))
                        else:
                            st.write("No open TCP ports found.")
                    else:
                        st.write("No TCP port information available.")
                else:
                    st.write("No nmap data available.")
                # --- Host-level nmap actions ---
                os_key = f"os_scan_{host}"
                if st.button("Run OS Detection & Version Scan", key=os_key):
                    try:
                        with st.spinner(f"Running OS and version scan for {host}..."):
                            os_nm = nmap.PortScanner()
                            os_result = os_nm.scan(hosts=host, arguments="-O -sV -T4")
                            host_data = os_nm[host]
                            # OS Guess
                            os_guess = "Unknown"
                            if 'osmatch' in host_data and host_data['osmatch']:
                                os_guess = host_data['osmatch'][0]['name']
                            st.write(f"**OS Guess:** {os_guess}")
                            # Service versions
                            if 'tcp' in host_data:
                                version_df = []
                                for port, portdata in host_data['tcp'].items():
                                    version_state = portdata.get('state', '')
                                    version_icon = '🟢' if version_state == 'open' else '🔴'
                                    version_df.append({
                                        'Port': port,
                                        'State': f"{version_icon} {version_state}",
                                        'Service': portdata.get('name', ''),
                                        'Product': portdata.get('product', ''),
                                        'Version': portdata.get('version', ''),
                                        'Extra Info': portdata.get('extrainfo', ''),
                                    })
                                if version_df:
                                    st.dataframe(pd.DataFrame(version_df))
                                else:
                                    st.write("No service version info found.")
                            else:
                                st.write("No TCP service version info available.")
                            # Traceroute (if supported)
                            traceroute_key = f"traceroute_{host}"
                            if st.button("Run Traceroute", key=traceroute_key):
                                try:
                                    with st.spinner(f"Running traceroute for {host}..."):
                                        tr_nm = nmap.PortScanner()
                                        tr_result = tr_nm.scan(hosts=host, arguments="--traceroute -T4")
                                        tr_data = tr_nm[host]
                                        if 'traceroute' in tr_data:
                                            hops = tr_data['traceroute'].get('hops', [])
                                            if hops:
                                                hop_df = []
                                                for hop in hops:
                                                    hop_df.append({
                                                        'Hop': hop.get('hop', ''),
                                                        'IP': hop.get('ipaddr', ''),
                                                        'RTT': hop.get('rtt', '')
                                                    })
                                                st.dataframe(pd.DataFrame(hop_df))
                                            else:
                                                st.write("No traceroute hops found.")
                                        else:
                                            st.write("Traceroute data not available.")
                                except Exception as e:
                                    st.error(f"Error running traceroute for {host}: {e}")
                    except Exception as e:
                        st.error(f"Error running OS/Version scan for {host}: {e}")
                st.divider()
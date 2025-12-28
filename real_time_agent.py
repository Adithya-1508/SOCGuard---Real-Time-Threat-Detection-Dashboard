import time
import json
import requests
import psutil
import win32evtlog
import win32evtlogutil
import win32con
import threading
from datetime import datetime

API_URL = "http://localhost:8000/api/ingest"

def send_event(source, message, ip="127.0.0.1", user=None, metadata=None):
    """Sends an event to the SOC Dashboard API."""
    payload = {
        "source": source,
        "message": message,
        "ip": ip,
        "user": user,
        "metadata": metadata or {}
    }
    try:
        requests.post(API_URL, json=payload, timeout=2)
        # print(f"[+] Sent: {message}")
    except Exception as e:
        print(f"[-] Failed to send event: {e}")

def monitor_system_logs():
    """Monitors Windows System Event Log for Warnings and Errors."""
    print("[*] Starting System Log Monitor...")
    server = 'localhost'
    log_type = 'System'
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    
    # Keep track of the last read time to avoid duplicates on restart (simple version)
    # For a real agent, we'd persist the last record number.
    last_time = datetime.now()

    while True:
        try:
            hand = win32evtlog.OpenEventLog(server, log_type)
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            
            for event in events:
                event_time = event.TimeGenerated.replace(tzinfo=None)
                
                # Only process new events (approximate)
                if event_time > last_time:
                    last_time = event_time
                    
                    # Filter for Warning (2) or Error (1)
                    if event.EventType in [win32con.EVENTLOG_ERROR_TYPE, win32con.EVENTLOG_WARNING_TYPE]:
                        msg = f"System Event: {event.SourceName} (ID: {event.EventID})"
                        send_event(
                            source="os_log",
                            message=msg,
                            metadata={"event_id": event.EventID, "source": event.SourceName, "type": event.EventType}
                        )
                        print(f"[LOG] {msg}")

            win32evtlog.CloseEventLog(hand)
        except Exception as e:
            print(f"[-] Log Monitor Error: {e}")
        
        time.sleep(5)

def monitor_processes():
    """Monitors for new suspicious processes."""
    print("[*] Starting Process Monitor...")
    existing_pids = set(p.pid for p in psutil.process_iter())
    
    suspicious_names = ["cmd.exe", "powershell.exe", "netcat.exe", "ncat.exe"]

    while True:
        current_pids = set(p.pid for p in psutil.process_iter())
        new_pids = current_pids - existing_pids
        
        for pid in new_pids:
            try:
                p = psutil.Process(pid)
                name = p.name().lower()
                if name in suspicious_names:
                    msg = f"Suspicious Process Started: {name} (PID: {pid})"
                    send_event(
                        source="endpoint_prevention",
                        message=msg,
                        user=p.username(),
                        metadata={"pid": pid, "cmdline": p.cmdline()}
                    )
                    print(f"[PROC] {msg}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        existing_pids = current_pids
        time.sleep(1)

def monitor_network():
    """Monitors for new TCP connections."""
    print("[*] Starting Network Monitor...")
    known_connections = set()
    
    while True:
        try:
            connections = psutil.net_connections(kind='tcp')
            current_connections = set()
            
            for conn in connections:
                if conn.status == 'ESTABLISHED':
                    conn_id = f"{conn.laddr.ip}:{conn.laddr.port}->{conn.raddr.ip}:{conn.raddr.port}"
                    current_connections.add(conn_id)
                    
                    if conn_id not in known_connections:
                        # New connection
                        msg = f"New Network Connection: {conn.raddr.ip}:{conn.raddr.port}"
                        send_event(
                            source="network_ids",
                            message=msg,
                            ip=conn.raddr.ip,
                            metadata={"local_port": conn.laddr.port, "remote_port": conn.raddr.port, "pid": conn.pid}
                        )
                        print(f"[NET] {msg}")
            
            known_connections = current_connections
        except Exception as e:
            print(f"[-] Network Monitor Error: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    print("=== Real-Time Threat Detection Agent ===")
    print("Press Ctrl+C to stop.")
    
    # Run monitors in separate threads
    t1 = threading.Thread(target=monitor_system_logs, daemon=True)
    t2 = threading.Thread(target=monitor_processes, daemon=True)
    t3 = threading.Thread(target=monitor_network, daemon=True)
    
    t1.start()
    t2.start()
    t3.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping agent...")

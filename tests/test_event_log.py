import win32evtlog
import win32evtlogutil
import win32security
import win32con

def read_security_log():
    server = 'localhost'
    log_type = 'System'
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

    try:
        hand = win32evtlog.OpenEventLog(server, log_type)
        print(f"Successfully opened {log_type} log.")
        
        events = win32evtlog.ReadEventLog(hand, flags, 0)
        print(f"Read {len(events)} events.")
        
        for event in events[:5]:
            print(f"Event ID: {event.EventID}")
            print(f"Source: {event.SourceName}")
            print(f"Time: {event.TimeGenerated}")
            print("-" * 20)
            
        win32evtlog.CloseEventLog(hand)
        return True
    except Exception as e:
        print(f"Failed to read log: {e}")
        return False

if __name__ == "__main__":
    read_security_log()

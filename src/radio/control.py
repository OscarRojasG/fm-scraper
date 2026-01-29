import threading

radio_thread = None
radio_stop_event = None
radio_lock = threading.Lock()

from channel import Server
import time, service

def wait_forever():
    try: 
        while True: time.sleep(0xFFFF)
    except KeyboardInterrupt: pass

service.log_init()
s = Server(5000)
s.serve(True)
wait_forever()
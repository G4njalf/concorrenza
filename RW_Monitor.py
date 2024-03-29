import threading
from pysm import monitor
import time

#per printare in modo atomico

class safeprint(monitor.monitor):
	def __init__(self):
		super().__init__()

	@monitor.entry
	def print(self, *args,**kwargs):
		print(*args,**kwargs)

safeprint = safeprint().print

class rwcontroller(monitor.monitor):
    def __init__(self,nr,nw):
        super().__init__()
        self.nr = nr
        self.nw = nw
        self.ok2read = monitor.condition(self)
        self.ok2write = monitor.condition(self)

    @monitor.entry
    def startRead(self):
        if self.nw > 0:
            self.ok2read.wait()
        self.nr += 1
        self.ok2read.signal()

    @monitor.entry
    def endRead(self):
        self.nr -= 1
        if self.nr == 0:
            self.ok2write.signal()

    @monitor.entry
    def startWrite(self):
        if self.nr > 0 or self.nw > 0:
            self.nw += 1
            self.ok2write.wait()
            self.nw -= 1
        self.nw += 1


    @monitor.entry
    def endWrite(self): 
        self.nw -= 1
        self.ok2read.signal()
        if self.nr == 0:
            self.ok2write.signal()


def reader1():
    while True:
        rwcontroller.startRead(rw)
        safeprint('reading1...')
        time.sleep(1)
        safeprint('finished R1...')
        rwcontroller.endRead(rw)
        

def reader2():
    while True:
        rwcontroller.startRead(rw)
        safeprint('reading2...')
        time.sleep(2)
        safeprint('finished R2...')
        rwcontroller.endRead(rw)
        

def writer1():
    while True:
        rwcontroller.startWrite(rw)
        safeprint('writing1...')
        time.sleep(1.5)
        safeprint('finished W1...')
        rwcontroller.endWrite(rw)
        

def writer2():
    while True:
        rwcontroller.startWrite(rw)
        safeprint('writing2...')
        time.sleep(1)
        safeprint('finished W2...')
        rwcontroller.endWrite(rw)
        
        
def writer3():
    while True:
        rwcontroller.startWrite(rw)
        safeprint('writing3...')
        time.sleep(2)
        safeprint('finished W3...')
        rwcontroller.endWrite(rw)
        

rw = rwcontroller(0,0)
w1 = threading.Thread(name='writer1', target=writer1)
w2 = threading.Thread(name='writer2', target=writer2)
w3 = threading.Thread(name='writer3', target=writer3)
r1 = threading.Thread(name='reader1', target=reader1)
r2 = threading.Thread(name='reader2', target=reader2)
w1.daemon=True
w2.daemon=True
w3.daemon=True
r1.daemon=True
r2.daemon=True
w1.start()
w2.start()
w3.start()
r1.start()
r2.start()
w1.join()
w2.join()
w3.join()
r1.join()
r2.join()


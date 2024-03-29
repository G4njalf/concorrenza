from pysm import monitor
from threading import Thread
from threading import Semaphore
import time
import queue

class safeprint(monitor.monitor):
	def __init__(self):
		super().__init__()

	@monitor.entry
	def print(self, *args,**kwargs):
		print(*args,**kwargs)

safeprint = safeprint().print

'''
il monitor AB gestisce l'accodamento limitato di due tipi di dati A e B. Il monitor prevede 3 procedure entry:
void AB.add2a(int a0, int a1)
void AB.addb(int b0)
void AB.geta2b(int *a0, int *b0, int *b1).
add2a aggiunge 2 elementi di tipo A, addb aggiunge un elemento di tipo B, geta2b restituisce un elemento di tipo A e
due di tipo B.
Il monitor può memorizzare al massimo MAX elementi di tipo A e MAX di tipo B. (MAX >= 2).
Se non sono disponibili almeno un elemento di tipo A e due di tipo B la funzione geta2b deve attendere.
Gli elementi devono essere restituiti in ordine FIFO così come le richieste pendenti per geta2b devono essere esaudite in
ordine FIFO.
'''

class AB(monitor.monitor):
    def __init__(self,MAX): # max >= 2 pls
        super().__init__()
        self.maxA = MAX  #numero massimo di a
        self.na = 0 #numero attuale di a
        self.maxB = MAX  #numero massimo di b
        self.nb = 0 #numero attuale di b
        self.memoa = []
        self.memob = []
        self.w8add2a = monitor.condition(self)
        self.w8addb = monitor.condition(self)
        self.w8geta2b = monitor.condition(self)



    @monitor.entry
    def add2a(self,a0,a1):
        if self.na + 2 > self.maxA :
            self.w8add2a.wait()
        self.memoa.append(a0)
        self.na = self.na + 1
        if self.na >= 1 and self.nb >= 2:
             self.w8geta2b.signal()
        self.memoa.append(a1)
        self.na = self.na + 1
        if self.na >= 1 and self.nb >= 2:
             self.w8geta2b.signal()
              
              
              

    @monitor.entry
    def addb(self,b0):
        if self.nb + 1 > self.maxB:
            self.w8addb.wait()
        self.memob.append(b0)
        self.nb = self.nb + 1
        if self.na >= 1 and self.nb >= 2:
             self.w8geta2b.signal()
              
    
    @monitor.entry
    def geta2b(self):
        if self.na < 1 or self.nb < 2:
            self.w8geta2b.wait()
        self.memoa.pop()
        self.na = self.na - 1
        if self.na + 2 <= self.maxA:
            self.w8add2a.signal() 
        self.memob.pop()
        self.nb = self.nb - 1
        if self.nb + 1 <= self.maxB:
             self.w8addb.signal() 
        self.memob.pop()
        self.nb = self.nb - 1
        if self.nb + 1 <= self.maxB:
             self.w8addb.signal() 


'''
Scrivere il monitor sv con una sola funzione entry syncvalue che ha la seguente dichiarazione:
procedure entry int syncvalue(int key);
I processi che chiamano la syncvalue si bloccano sempre. Quando il valore del parametro key è diverso da quello della
precedente chiamata il processo prima di bloccarsi riattiva tutti i processi in attesa. Il valore di ritorno è il numero di
processi con lo stesso valore key sbloccati. Per esempio:
P chiama sv.syncvalue(42), si blocca.
Q chiama sv.syncvalue(42), si blocca.
R chiama sv.syncvalue(44) sblocca P e Q poi si blocca. Il valore di ritorno per P e Q è 2.
T chiama sv.syncvalue(46), sblocca R che ritorna 1 e si blocca.
Q chiama sv.syncvalue(46), si blocca.
P chiama sv.syncvalue(46), si blocca
V chiama sv.syncvalue(0), sblocca T, Q e P (valore di ritorno: 3) poi si blocca...
'''

class sv(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.lastkey = 0
        self.numsamekey = 0
        self.w8 = monitor.condition(self)


    @monitor.entry
    def syncvalue(self,key):
        returnvalue = 0
        if self.lastkey == key:
            self.numsamekey = self.numsamekey + 1
            returnvalue = self.numsamekey
            self.lastkey = key
            self.w8.wait()
        else:    
            for _ in range(self.numsamekey):
                self.w8.signal()
            self.numsamekey = 0
            self.lastkey = key
            self.numsamekey = self.numsamekey + 1
            returnvalue = self.numsamekey
            self.w8.wait()
        returnvalue = self.numsamekey
        return returnvalue
    

'''
Scrivere il monitor rb (redblack) con due procedure entry:
float meanblack(float v)
float meanred(float v)
Esistono due tipi di processo, neri e rossi. I processi neri chiamano la funzione meanblack mentre i processi rossi
chiamano meanred.
Entrambe le funzioni restituiscono la media dei valori passati da una chiamata di meanblack e una di meanred.
Per fare il calcolo ogni chiamata di un processo rosso (meanred) deve sincronizzarsi con una chiamata di un processo
nero (meanblack) e viceversa. Se la prima chiamata è una meanblack il processo chiamante attende, quando
successivamente un processo rosso chiama meanred entrambi i processi si sbloccano ed entrambe le funzioni devono
restituire lo stesso valore (la media dei valori del parametro v). Se non arrivano chiamate di meanred i processi neri che
chiamano meanblack devono attendere in ordine FIFO. Lo stesso vale anche per i processi meanred fino ad una
chiamata di meanblack.
Il monitor rb deve usare una sola variabile di condizione e nessuna coda/lista/array, solo valori scalari (int o float).
'''


class rb(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.redw8 = 0
        self.blackw8 = 0  # contatore processi bloccati
        self.vred = 0
        self.vblack = 0
        self.condition = monitor.condition(self)
    
    @monitor.entry
    def meanblack(self,v):
        if self.blackw8 > 0:
            self.blackw8 += 1
            self.condition.wait()
            self.blackw8 = False
        if self.redw8:
            self.vblack = v
            self.condition.signal()
            vred = self.vred
            self.vred = 0
            return (vred + v ) / 2
        self.blackw8 = True
        self.vblack = v
        self.condition.wait()
        self.blackw8 = False
        vred = self.vred
        self.vred = 0
        return (vred + v) / 2
    
    @monitor.entry
    def meanred(self,v):
        if self.redw8:
            self.condition.wait()
            self.redw8 = False
        if self.blackw8:
            self.vred = v
            self.condition.signal()
            vblack = self.vblack
            self.vblack = 0
            return (vblack + v ) / 2
        self.redw8 = True
        self.vred = v
        self.condition.wait()
        self.redw8 = False
        vblack = self.vblack
        self.vblack = 0
        return (vblack + v) / 2  


themonitor = rb()

def p1():
    time.sleep(2)
    safeprint(themonitor.meanblack(2),"<-p1")
    

def p2():
    time.sleep(2)
    safeprint(themonitor.meanred(4),"<-p2")
    

def p3():
    
    safeprint(themonitor.meanblack(6),"<-p3")
    safeprint(themonitor.meanblack(6),"<-p3")
    return


    

t1=Thread(target=p1)
t2=Thread(target=p2)
t3=Thread(target=p3)


t1.start()
t2.start()
t3.start()
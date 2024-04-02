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


'''
Scrivere, facendo uso di semafori, la funzione syncvalue che ha la seguente dichiarazione:
void syncvalue(int key);
I processi che chiamano la syncvalue si bloccano sempre. Quando il valore del parametro key è diverso da quello della
precedente chiamata il processo prima di bloccarsi riattiva tutti i processi in attesa. Per esempio:
P chiama syncvalue(42), si blocca.
Q chiama syncvalue(42), si blocca.
R chiama syncvalue(44) sblocca P e Q poi si blocca.
T chiama syncvalue(46), sblocca R e si blocca.
P chiama syncvalue(46), si blocca.
V chiama syncvalue(0), sblocca T e P poi si blocca...
'''
s = Semaphore(0)
mutex = Semaphore(1)
blocked = 0
memokey = -1

def syncvalue(key):
    global memokey, blocked
    mutex.acquire()
    if memokey != key:
        memokey = key
        for _ in range(blocked):
            s.release()
        blocked += 1
        mutex.release()
        s.acquire()
        blocked -= 1
        return
    else:
        blocked += 1
        mutex.release()
        s.acquire()
        blocked -= 1
    return



'''
Scrivere il monitor cs che fornisca un servizio di elaborazione client-server.
I molteplici "clienti" chiedono elaborazioni ai server eseguendo la seguente funzione:
def service_request(data):
 return cs.request(data)
mentre i server eseguono il codice:
process server(i: i = 0,...,NSERVER-1):
 while True:
 data = cs.get_request(i)
 cs.send_result(i, process(data))
Quando un server è libero chiede una nuova richiesta da elaborare (funzione get_request), se non ci sono richieste da
elaborare attende che un cliente ne sottoponga una (tramite la funzione request). Se vi sono uno o più richieste in attesa
di essere elaborate get_request restituisce i dati (argomento data) della prima.
Dopo che il server ha elaborato la richiesta (funzione process) il risultato viene passato al monitor tramite la funzione
send_result che lo restituisce al cliente come valore di ritorno della funzione request.
'''

class cs(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.pendingrequests = 0
        self.conditionserver = monitor.condition(self)
        self.conditionclient = monitor.condition(self)
        self.requests = []
        self.data = 0
    
    @monitor.entry
    def getrequest(self):  #la chiama il server per prendere una request da un client
        if self.pendingrequests > 0:
            data = self.requests.pop()
            self.pendingrequests -= 1
            return data
        self.conditionserver.wait()
        data = self.requests.pop()
        self.pendingrequests -= 1
        return data

    @monitor.entry
    def request(self,data): # la chiama il client per fare una richiesta al server
        self.requests.insert(0,data)
        self.pendingrequests += 1
        self.conditionserver.signal()
        self.conditionclient.wait()
        return self.data

    @monitor.entry
    def sendresult(self,data): # la chiama il server dopo aver elaborato la richiesta il monitor la restituira al cliente come return di request
        self.data = data
        self.conditionclient.signal()


'''
Scrivere il monitor redblack che fornisce una procedure entry:
#define red 0
#define black 1
double rb(int color, double value)
I processi che usano il monitor redblack devono sincronizzarsi in modo che completino l'esecuzione di rb in modo
alternato: se l'ultimo processo che ha completato rb aveva indicato il colore rosso il prossimo sia nero e viceversa.
(in altre parole mai due processi che avevano chiamato rb con lo stesso colore possono proseguire uno dopo l'altro
Il valore di ritorno di rb deve essere la media dei valori dei parametri "value" delle chiamate rb di colore "color" che sono
state sbloccate.
Esempio: La chiamata rb(red, 2) non si blocca e ritorna 2, successivamente rb(red, 4) si blocca perché l'ultima
sbloccata è rossa. Poi rb(black, 5) non si blocca perché l'ultima è rossa e ritorna 5 ma a questo punto si può sbloccare
anche la chiamata precedente rb(red, 4) e il valore ritornato è 3 (la media fra 2 e 4). 
'''

class redblack(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.condition = monitor.condition(self)
        self.color = None
        self.sumred = 0
        self.sumblack = 0
        self.numberred = 0
        self.numberblack = 0

    @monitor.entry
    def rb(self,color,value):
        if self.color == color:
            if color == 0: #red
                self.sumred = self.sumred + value
                self.numberred += 1
                self.condition.wait()
                return self.sumred / self.numberred
            else: #black
                self.sumblack = self.sumblack + value
                self.numberblack += 1
                self.condition.wait()
                return self.sumblack / self.numberblack
        if color == 0: # red
            self.color = color
            self.sumred = self.sumred + value
            self.numberred += 1
            self.condition.signal()
            return value
        else: # black
            self.color = color
            self.sumblack = self.sumblack + value
            self.numberblack += 1
            self.condition.signal()
            return value


'''
Scrivere il monitor fullbuf che abbia le seguenti procedure entry:
void add(int value)
int get(void)
Le prime MAX chiamate della procedure entry add devono bloccare i processi chiamanti. In seguito deve sempre valere
Na >= MAX indicando con Na il numero di processi bloccati in attesa di completare la funzione add.
La funzione get deve attendere che Na > MAX, restituire la somma algebrica dei parametri value delle chiamate add in
sospeso e riattivare il primo processo in attesa di completare la add (se la get richiede che Na > MAX, la get può
riattivare un processo e al completamento della get si rimarrà garantito che Na >= MAX)
'''

class fullbuf(monitor.monitor):
    def __init__(self):
        self.max = 10
        self.na = 0 #numero processi bloccati in attesa di completare la funzione add
        self.sum = 0
        self.condition = monitor.condition(self)
        super().__init__()

    @monitor.entry
    def add(self,value):
        if self.na < self.max:
            self.na += 1
            self.sum = self.sum + value
            self.condition.wait()
        return
    
    @monitor.entry
    def get(self):
        if(self.na > self.max):
            return self.sum


themonitor = redblack()


def p1():
    safeprint("p1 ->",themonitor.rb(0,10))

def p2():
    safeprint("p2 ->",themonitor.rb(1,20))

def p3():
    safeprint("p3 ->",themonitor.rb(1,5))

t1=Thread(target=p1)
t2=Thread(target=p2)
t3=Thread(target=p3)

t1.start()
t2.start()
t3.start()
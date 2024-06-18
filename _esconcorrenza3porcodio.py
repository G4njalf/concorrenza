from pysm import monitor
from threading import Thread
from threading import Semaphore
import time

class safeprint(monitor.monitor):
	def __init__(self):
		super().__init__()

	@monitor.entry
	def print(self, *args,**kwargs):
		print(*args,**kwargs)

safeprint = safeprint().print

'''
Scrivere il monitor rgbsum che fornisce una procedure entry:
#define red 0
#define green 1
#define blue 2
double rgb(int color, double value)
I processi che usano il monitor rgbsum devono sommare i valori delle sequenze di chiamate dello stesso colore (red,
green o blue). La funzione rgb è sempre bloccante. Solo quando una sequenza di chiamate dello stesso colore viene
interrotta da una chiamata di colore diverso tutti i processi in attesa vengono sbloccati e rgb restituisce la somma dei
parametri 'value'.
Esempio: Il processo P chiama rgb(red, 2) -> si blocca. il processo Q chiama rgb(red, 4) ->si blocca. Il processo R chiama
rgb(blue, 1) sblocca i due processi P e Q che hanno chiamato rgb con parametro red, ad entrambi rgb ritorna il valore 6
(2 + 4). poi R si blocca. se ora un altro processo T chiama rgb(green, 39) il processo R continua e rgb ritorna 1 mentre R si
ferma. Ora i processi W,X,Y chiamano tutti rgb(green, 1) bloccandosi. Il processo Z chiamando rgb(red, 0) sblocca R,W,X,Y,
rgb restituisce a questi processi il valore 42 e Z si ferma.
'''

class rgbsum(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.color = -1
        self.value = 0
        self.blockedproc = 0
        self.condition = monitor.condition(self)
    
    @monitor.entry
    def rgb(self,color,value):
        if color != self.color :
            if self.blockedproc > 0: 
                for _ in range(self.blockedproc):
                    self.condition.signal()
                self.value = 0
                self.blockedproc = 0
            self.value = self.value + value
            self.color = color
            self.blockedproc += 1
            self.condition.wait()
        else:
            self.value = self.value + value
            self.color = color
            self.blockedproc += 1
            self.condition.wait()
        return self.value


'''
Scrivere il monitor ab12 che gestisce due buffer limitati FIFO, il primo memorizza elementi di tipo tipoa il
secondo elementi di tipo tipob. Entrambi i buffer contengono al massimo MAX elementi.
Il monitor ab12 fornisce quattro procedure entry:
void adda(tipoa a1, tipoa a2): aggiunge due elementi al primo buffer.
void addb(tipob b1): aggiunge un elemento al secondo buffer.
tipoa getone(void): restituisce un elemento dal primo buffer.
(tipoa, tipob) getab(void): restituisce un elemento dal primo buffer e uno dal secondo.
Tute le chiamate possono essere bloccanti (se non c'è spazio per inserire elementi nel caso delle chiamate di tipo add, se
non ci sono gli elementi da restituire per le chiamate di tipo get). Le richieste devono essere soddisfatte in ordine FIFO
'''


class ab12(monitor.monitor):
    def __init__(self):
         super().__init__()
         self.max = 5
         self.buffa = []
         self.counta = 0
         self.buffb = []
         self.countb = 0
         self.oka = monitor.condition(self)
         self.okb = monitor.condition(self)

    @monitor.entry
    def adda(self,a1,a2):
        if self.counta+2 > self.max :
            self.oka.wait()
        else:
            self.buffa.append(a1)
            self.buffa.append(a2)
            self.counta += 2
            self.oka.signal() 
        return
    
    @monitor.entry
    def addb(self,b1):
        if self.countb+1 > self.max :
            self.okb.wait()
        else:
            self.buffb.append(b1)
            self.countb += 1
            self.okb.signal()

    @monitor.entry
    def getoneA(self):
        if self.counta < 1:
            self.oka.wait()
        else:
            x = self.buffa.pop()
            self.counta -= 1
            if self.counta + 2 <= self.max:
                 self.oka.signal()
        return x
    
    @monitor.entry
    def getab(self):
        if self.counta < 1:
            self.oka.wait()
        if self.countb < 1 :
             self.okb.wait()
        else:
            x = self.buffa.pop()
            self.counta -= 1
            if self.counta + 2 <= self.max:
                 self.oka.signal()
            y = self.buffb.pop()
            self.countb -= 1
            if self.countb +1 <= self.max:
                self.okb.signal()
        return (x,y)



'''
Scrivere il monitor ds (dispatchstring) che consenta di trasferire stringhe di caratteri fra processi. Il monitor
ha quattro procedure entry:
void startsend(void)
void sendchar(char c)
void startrecv(void)
char recvchar(void)
Quando un processo vuole spedire una stringa chiama la funzione startsend poi tramite sendchar spedisce uno ad
uno i caratteri della stringa e infine il carattere 0 per indicare la fine della stringa. Similmente quando un processo vuole
ricevere una stringa chiama la funzione startrecv, riceve uno ad uno i caratteri usando la recvchar. La ricezione del
carattere 0 indica la fine della stringa.
Il monitor trasferisce una stringa alla volta e deve usare un buffer di un solo carattere (non può memorizzare vettori o
stringhe di caratteri).
'''

class ds(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.char = None  # Inizialmente il buffer è vuoto
        self.condsend = monitor.condition(self)
        self.condrecv = monitor.condition(self)

    @monitor.entry
    def startsend(self):
        pass  # Potrebbe non fare nulla

    @monitor.entry
    def sendchar(self, char):
        while self.char is not None:  # Aspetta finché il buffer non è vuoto
            self.condsend.wait()
        self.char = char
        self.condrecv.signal()  # Segnala che c'è un nuovo carattere nel buffer

    @monitor.entry
    def startrecv(self):
        pass  # Potrebbe non fare nulla

    @monitor.entry
    def recvchar(self):
        while self.char is None:  # Aspetta finché il buffer non è pieno
            self.condrecv.wait()
        char = self.char
        self.char = None  # Svuota il buffer
        self.condsend.signal()  # Segnala che il buffer è vuoto
        return char





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
        self.key = None
        self.blockedcount = 0
        self.condition = monitor.condition(self)
    
    @monitor.entry
    def syncvalue(self,key):
        if self.key != key:
            if self.blockedcount > 0:
                for _ in range(self.blockedcount):
                    self.condition.signal()
                self.blockedcount = 1
                self.key = key
                self.condition.wait()
            else:
                self.key = key
                self.blockedcount +=1
                self.condition.wait()
        else:
            self.blockedcount +=1
            self.condition.wait()
        return self.blockedcount


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
Il monitor rb deve usare una sola variabile di condizione e nessuna coda/lista/array, solo valori scalari (int o float)
'''

class rb(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.condition = monitor.condition(self)
        self.red = 0
        self.black = 0
        
    
    @monitor.entry
    def meanblack(self,v):
        if self.black != 0:
            self.condition.wait()
        else:
            self.black = v
            self.condition.signal()
            if self.red == 0:
                self.condition.wait()
                black = self.black
                red = self.red
                self.black = 0
                self.red = 0
                return (black + red)/2
            else:
                return (black + red)/2
    
    @monitor.entry
    def meanred(self,v):
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
Dopo che il server ha elaborato la richiesta (funzione process) il risultato viene passsato al monitor tramite la funzione
send_result che lo restituisce al cliente come valore di ritorno della funzione request.
'''



mon = rb()

def p1():
    safeprint(mon.meanblack(3))
    time.sleep(1)
    safeprint(mon.meanblack(4))

def p2():
    time.sleep(1)
    safeprint(mon.meanred(2))
    safeprint(mon.meanred(1))

def p3():
    time.sleep(1)



t1=Thread(target=p1)
t2=Thread(target=p2)
t3=Thread(target=p3)

t1.start()
t2.start()
t3.start()
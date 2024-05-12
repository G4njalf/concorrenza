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


'''
Scrivere il monitor synmsg che consenta uno scambio di messaggi fra due processi in maniera sincrona.
Il processo produttore esegue il seguente codice.
producer: process:
 while True:
 msg_t msg = produce_new_msg()
 synmsg.send(&msg)
e il processo consumatore:
consumer: process:
 while True:
 msg_t msg
 synmsg.recv(&msg)
 consume_msg(&msg)
Come si vede le procedure entry hanno come parametro l'indirizzo del messaggio:
procedure entry void send(msg_t *msg)
procedure entry void recv(msg_t *msg)
Il monitor deve trasferire il contenuto del messaggio direttamente fra i processi usando la funzione:
void copymsg(msg_t *src, msg_t *dest)
(Il monitor non deve avere buffer di tipo msg_t ma solo variabili di tipo puntatore a msg_t.)
'''

class synmsg(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.msg = ""
        self.conditionSend = monitor.condition(self)
        self.conditionRcv = monitor.condition(self)

    @monitor.entry
    def send(self,msg):
        self.msg = msg
        self.conditionRcv.signal()
        if self.msg == "":
            self.conditionRcv.signal()
        else:
            self.conditionSend.wait()

    
    @monitor.entry
    def recieve(self,msg):
        msg = self.msg
        self.msg = ""
        if msg != "":
            self.conditionSend.signal()
        else:
            self.conditionRcv.wait()
            msg = self.msg
            self.msg = ""
            self.conditionSend.signal()
        return msg



'''
Facendo uso di semafori scrivere un funzione wait4 che faccia proseguire i processi a blocchi di quattro: il
primo processo che chiama la wait4 si deve fermare, così come il secondo e il terzo. Il quarto processo deve far
proseguire tutti e quattro i processi. In uguale modo l'ottavo processo che chiama wait4 risveglierà anche il quinto, il
sesto e il settimo.
SI chiede:
* che l'implementazione non faccia uso di code o di altre strutture dati ma solamente di contatori (e ovviamente
semafori)
* che la soluzione faccia uso del passaggio del testimone per garantire che vengano riattivati i processi corretti e non
altri.
'''
s = [Semaphore(0),Semaphore(0),Semaphore(0)]
mutex = Semaphore(1)
counter = 0
def wait4():
    global counter,mutex,s
    mutex.acquire()
    if counter < 3:
        counter += 1
        mutex.release()
        s[counter-1].acquire()
        return
    for _ in range(3):
        s[_].release()
    counter = 0
    mutex.release()

'''
Usando i semafori implementare un servizio che preveda due funzioni:
 void sumstop(int v)
 int sumgo(void)
La funzione sumstop deve mettere il processo chiamante in attesa.
La funzione sumgo deve sbloccare tutti i processi messi in attesa con la sumstop e restituire la somma algebrica dei
valori passati come parametro alla sumstop dai processi che sono stati sbloccati (zero se la sumgo viene richiamate
quando non c'è nessun processo bloccato).

'''
mutex = Semaphore(1)
s = Semaphore(0)
sum = 0
counter = 0
def sumstop(v):
    global mutex,s,sum,counter
    mutex.acquire()
    sum = sum + v
    counter += 1
    mutex.release()
    s.acquire()
    return 

def sumgo():
    global mutex,s,sum,counter
    mutex.acquire()
    tmp = sum
    sum = 0
    for _ in range(counter):
        s.release()
    counter = 0
    mutex.release()
    return tmp


'''
In un porto con una sola banchina utilizzabile occorre caricare cereali sulle navi. I camion portano i cereali
al porto. Una sola nave alla volta può essere attraccata al molo, un solo camion alla volta scarica i cereali nella nave.
Il codice eseguito da ogni nave è:
nave[i] process:
 porto.attracca(capacità)
 porto.salpa()
 ...naviga verso la destinazione
Il codice di ogni camion è:
camion[j] process:
 while (1):
 quantità = carica_cereali()
 porto.scarica(quantità)
I camion fanno la spola dai depositi alla nave. La nave arriva vuota e può salpare solo se è stata completamente
riempita (la somma delle quantità scaricate dai camion raggiunge la capacità indicata come parametro della funzione
attracca). Se un camion può scaricare solo parzialmente il suo carico rimane in porto e aspetta di completare
l'operazione con la prossima nave che attraccherà al molo.
Scrivere il monitor porto.
'''

class porto(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.oknave = monitor.condition(self)
        self.okcamion = monitor.condition(self)
        self.maxnave = 0
        self.maxcamion = 0
        self.actualnave = 0
        self.actualcamion = 0


    @monitor.entry
    def attracca(self,capnave):
        self.maxnave = capnave
        self.okcamion.signal()
        if self.actualcamion == 0:
            self.oknave.wait()
        return
    
    @monitor.entry
    def salpa(self):
        if self.maxnave != self.actualnave:
            self.oknave.wait()
        return
    
    @monitor.entry
    def scarica(self,capcamion):
        self.maxcamion = capcamion
        self.actualcamion = capcamion
        if self.maxnave == 0:
            self.okcamion.wait()
        if self.actualnave + self.actualcamion <= self.maxnave: #ci sta tutto il camion
            self.actualnave = self.actualcamion + self.actualnave
        else: #non ci sta tutto il camion
            resnave = self.maxnave - self.actualnave
            self.actualcamion = self.actualcamion - resnave
            self.actualnave = self.maxnave
            self.oknave.signal()


'''
Scrivere il monitor collocamento:
void cercolavoro(char *nome, char *skill)
void char *assumo(char * skill)
Quando un processo chiama la cercolavoro si mette in attesa di una richiesta di lavoro e rimane bloccato nel monitor
fino a che non è stato assunto. Nella cercolavoro viene indicato il nome dell'aspirante lavoratore la sua capacità (skill).
Un datore di lavoro con necessità di personale chiama la assumo specificando la capacità richiesta. Se c'è in attesa
almeno un aspirante lavoratore con quella specifica capacità (uguale valore di skill), il datore di lavoro riceve il nome del
nuovo dipendente ed entrambi i processi escono dal monitor. Nel caso non ci siano richieste compatibili il datore di
lavoro si blocca nel monitor attendendo un lavoratore con la capacità cercata. Quando arriva il lavoratore che soddisfa
le richieste si sbloccano entrambi i processi lavoratore e datore di lavoro. La assumo restituisce in ogni caso il nome del
dipendente da assumere.
'''

class collocamento(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.countsearch = 0
        self.search =[[],[]]
        self.req =[]
        self.conditionassum = monitor.condition(self)
        self.conditionsearch = monitor.condition(self)


    @monitor.entry
    def cercolavoro(self,nome,skill):
        self.countsearch += 1
        self.search[0].append(nome)
        self.search[1].append(skill)
        for element in self.req:
            if element in self.search[1]:
                self.conditionassum.signal()
        self.conditionsearch.wait()
        self.countsearch -= 1
        return


    @monitor.entry
    def assumo(self,skill):
        self.req.append(skill)
        it = 0
        for element in self.search[1]:
            if element in self.req:
                sk = self.search[1].pop(it)
                nm = self.search[0].pop(it)
                self.req.remove(skill)
                self.conditionsearch.signal()
                for _ in range(self.countsearch):
                    self.conditionsearch.signal()
                    return (nm,sk)
            it += 1
        self.conditionassum.wait()
        it = 0
        for element in self.search[1]:
            if element in self.req:
                sk = self.search[1].pop(it)
                nm = self.search[0].pop(it)
                self.req.remove(skill)
                self.conditionsearch.signal()
            it += 1
        for _ in range(self.countsearch):
            self.conditionsearch.signal()
        return (nm,sk)


'''
Scrivere il monitor delay che fornisce due procedure entry:
int wait_tick(int nticks)
void tick(void)
La procedure entry tick è pensata per essere richiamata periodicamente (es. ogni secondo o ora o giorno) da un
processo.
Quando un processo chiama la wait_tick deve attendere un numero di chiamate della tick pari al parametro nticks.
Per esempio se un processo chiama wait_tick(2) deve fermarsi e verrà riattivato alla seconda successiva chiamata di
tick.
La funzione wait_tick ha come valore di ritorno il numero di processi che erano bloccati al momento della tick che ha
sbloccato il chiamante.
Esempio: P chiama wait_tick(2) e si blocca. Q chiama wait_tick(3) e si blocca. T chiama tick() non succede nulla. R
chiama wait_tick(2) e si blocca. T chiama tick(), viene sbloccata la wait_tick di P e il valore ritornato è 3. T chiama
tick(), vengono sbloccate le wait_tick di Q e R e il valore ritornato per entrambi i processi è 2
'''

class delay(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.blockedproc = 0
        self.nticks = 0
        self.mem = 0 
        self.condition = monitor.condition(self)
        self.list = [[],[]]  #(nticks,ticksvisti)
    
    @monitor.entry
    def wait_tick(self,nticks):
        self.list[0].append(nticks)
        self.list[1].append(0)
        self.blockedproc += 1
        self.condition.wait()
        idx = self.list[0].index(nticks)
        self.list[0].pop(idx)
        self.list[1].pop(idx)
        self.mem = self.blockedproc
        self.blockedproc -=1
        return self.mem
    
    @monitor.entry
    def tick(self):
        if self.blockedproc == 0:
            return
        for i in range(len(self.list[0])):
            self.list[1][i] +=1
        if self.list[0][0] == self.list[1][0]:
            self.condition.signal()
            self.mem = 0
        return


'''
Scrivere il monitor semdata che implementi un semaforo con dato. Questa astrazione prevede due
operazioni:
 datatype dP(void);
 void dV(datatype data);
Non è previsto assegmento di valore iniziale nel costruttore, l'invariante è lo stesso dei semafori (con init = 0): ndP <=
ndV (dove ndP e ndV rappresentano rispettivamente il numero di operazioni dP e dV completate. I dati passati come
parametro alla dV devono essere memorizzati in ordine LIFO. L'operazione nP restituisce il valore più recente fra quelli
memorizzati (e lo cancella dalla struttura dati).
'''

class semdata(monitor.monitor):
    def __init__(self):
        super().__init__()
        self.data = [] #in ordine LIFO
        self.condition = monitor.condition(self)


    @monitor.entry
    def dp(self):
        if len(self.data) == 0:
            self.condition.wait()
        return self.data.pop(0)
    
    @monitor.entry
    def dv(self,data):
        self.data.insert(0,data)
        self.condition.signal()
        return



'''
Scrivere il monitor multibuf che implementi un buffer limitato (MAX elementi) di oggetti di tipo T che
implementi le seguenti procedure entry:
void add(int n, T objexts[]);
void get(int n, T objects[]);
La funzione add deve aggiungere al buffer gli n oggetti passati col parametro objects. La funzione get deve predere
dal buffer in modalità FIFO i primi n elementi presenti nel buffer e copiarli negli elementi del vettore objects.
Entrambe le funzioni devono attendere che vi siano le condizioni per poter essere completate: che ci siano n elementi
liberi per la add, che ci siano n elementi nel buffer per la get. Non sono ammesse esecuzioni parziali: mentre attendono
le rispettive condizioni nessun elemento può essere aggiunto o rimosso dal buffer.
La definizione del problema C.1 presenta casi di possibile deadlock? quali?
'''

class multibuf(monitor.monitor):
    def __init__(self,max):
        super().__init__()
        self.max = max
        self.n = max
        self.buff = []
        self.condition1 = monitor.condition(self)
        self.condition2 = monitor.condition(self)

    @monitor.entry
    def add(self,obj):
        if len(self.buff) + len(obj) > self.max:
            self.condition1.wait()
        self.buff.extend(obj)
        if len(self.buff) >= self.n:
            self.condition2.signal()
        return
    
    @monitor.entry
    def get(self,n,obj):
        self.n = n
        if len(self.buff) < n:
            self.condition2.wait()
        for _ in range(n):
            obj.append(self.buff.pop(0))
        self.condition1.signal()
        return obj  





mon = multibuf(4)



def p1():
    while True:
        ob = []
        mon.get(3,ob)
def p2():
    while True:
        ob = [3,2,1,0]
        mon.add(ob)
def p3():
    while True:
        ob = [9,8,7]
        mon.add(ob)



t1=Thread(target=p1)
t2=Thread(target=p2)
t3=Thread(target=p3)


t1.start()
t2.start()
t3.start()


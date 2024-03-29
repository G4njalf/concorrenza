from threading import Thread
from pysm import monitor
from threading import Semaphore
import queue
import time

class safeprint(monitor.monitor):
	def __init__(self):
		super().__init__()

	@monitor.entry
	def print(self, *args,**kwargs):
		print(*args,**kwargs)

safeprint = safeprint().print


#15 febbraio 2023

#Esercizio c.1: Scrivere il monitor redblack che fornisce una procedure entry:
##define red 0
##define black 1
#double rb(int color, double value)
#I processi che usano il monitor redblack devono sincronizzarsi in modo che completino l'esecuzione di rb in modo
#alternato: se l'ultimo processo che ha completato rb aveva indicato il colore rosso il prossimo sia nero e viceversa.
#(in altre parole mai due processi che avevano chiamato rb con lo stesso colore possono proseguire uno dopo l'altro
#Il valore di ritorno di rb deve essere la media dei valori dei parametri "value" delle chiamate rb di colore "color" che sono
#state sbloccate.
#Esempio: La chiamata rb(red, 2) non si blocca e ritorna 2, successivamente rb(red, 4) si blocca perché l'ultima
#sbloccata è rossa. Poi rb(black, 5) non si blocca perché l'ultima è rossa e ritorna 5 ma a questo punto si può sbloccare
#anche la chiamata precedente rb(red, 4) e il valore ritornato è 3 (la media fra 2 e 4). 


red = 0
black = 1

class redblack(monitor.monitor):

	def __init__(self):
		super().__init__()
		self.lastcolor = None
		self.okcolor = []
		self.okcolor.append(monitor.condition(self))
		
	@monitor.entry
	def rb(self,color,value):
		if color == self.lastcolor:
			self.okcolor[0].wait()
			time.sleep(0.5)
		else:
			self.lastcolor = color
			self.okcolor[0].signal()
		return color
	

#20 gennaio 2023

#Esercizio c.1: Scrivere il monitor fullbuf che abbia le seguenti procedure entry:
#void add(int value)
#int get(void)
#Le prime MAX chiamate della procedure entry add devono bloccare i processi chiamanti. In seguito deve sempre valere
#Na >= MAX indicando con Na il numero di processi bloccati in attesa di completare la funzione add.
#La funzione get deve attendere che Na > MAX, restituire la somma algebrica dei parametri value delle chiamate add in
#sospeso e riattivare il primo processo in attesa di completare la add (se la get richiede che Na > MAX, la get può
#riattivare un processo e al completamento della get si rimarrà garantito che Na >= MAX)

class fullbuf(monitor.monitor):
	def __init__(self,maxx):
		super().__init__()
		self.maxx = maxx
		self.Na = 0
		self.condadd = monitor.condition(self)
		self.condget = monitor.condition(self)
		self.fullvalue = 0
	
	@monitor.entry
	def add(self,value):
		self.Na = self.Na + 1
		if self.Na <= self.maxx:
			self.fullvalue = value + self.fullvalue
			self.condadd.wait()
			self.fullvalue = self.fullvalue-value
			self.Na = self.Na -1
		self.condget.signal()
		return
	
	@monitor.entry
	def get(self):
		self.condget.wait()
		mem = self.fullvalue
		self.condadd.signal()
		return mem
	

#18 gennaio 2023

#Esercizio c.2: Facendo uso di semafori scrivere un funzione wait4 che faccia proseguire i processi a blocchi di quattro: il
#primo processo che chiama la wait4 si deve fermare, così come il secondo e il terzo. Il quarto processo deve far
#proseguire tutti e quattro i processi. In uguale modo l'ottavo processo che chiama wait4 risveglierà anche il quinto, il
#sesto e il settimo.
#SI chiede:
#* che l'implementazione non faccia uso di code o di altre strutture dati ma solamente di contatori (e ovviamente
#semafori)
#* che la soluzione faccia uso del passaggio del testimone per garantire che vengano riattivati i processi corretti e non
#altri.

s = Semaphore(0)
mutex = Semaphore(1)
c = 0
def wait4():
	global c
	mutex.acquire()
	c = c + 1
	if c >= 4:
		c = c-1
		s.release()
	else:
		mutex.release()
		s.acquire()
		c = c-1
		if c > 0:
			s.release()
		else:
			mutex.release()

#18 gennaio 2023

#Esercizio c.1: Scrivere il monitor synmsg che consenta uno scambio di messaggi fra due processi in maniera sincrona.
#Il processo produttore esegue il seguente codice.
#producer: process:
# while True:
# msg_t msg = produce_new_msg()
# synmsg.send(&msg)
#e il processo consumatore:
#consumer: process:
# while True:
# msg_t msg
# synmsg.recv(&msg)
# consume_msg(&msg)
#Come si vede le procedure entry hanno come parametro l'indirizzo del messaggio:
#procedure entry void send(msg_t *msg)
#procedure entry void recv(msg_t *msg)
#Il monitor deve trasferire il contenuto del messaggio direttamente fra i processi usando la funzione:
#void copymsg(msg_t *src, msg_t *dest)
#(Il monitor non deve avere buffer di tipo msg_t ma solo variabili di tipo puntatore a msg_t.)

class synmsg(monitor.monitor):
	def __init__(self):
		super().__init__()
		self.cond = monitor.condition(self)
		self.dest = None
		self.src = None
	def copymsg(self,src,dest):
		dest = src
		self.dest = dest
	
	@monitor.entry
	def send(self,msg):
		self.src = msg
		self.copymsg(self.src,None)
		self.cond.signal()
	
	@monitor.entry
	def recv(self,msg):
		self.cond.wait()
		msg = self.dest
		return msg


s = synmsg()

def producer():
	while True:
		msg = "messaggio"
		s.send(msg)
		time.sleep(1)

def consumer():
	while True:
		msg = None
		safeprint(s.recv(msg))


#06 settembre 2022

#Esercizio c.2: Usando i semafori implementare un servizio che preveda due funzioni:
# void sumstop(int v)
# int sumgo(void)
#La funzione sumstop deve mettere il processo chiamante in attesa.
#La funzione sumgo deve sbloccare tutti i processi messi in attesa con la sumstop e restituire la somma algebrica dei
#valori passati come parametro alla sumstop dai processi che sono stati sbloccati (zero se la sumgo viene richiamate
#quando non c'è nessun processo bloccato).

mutex = Semaphore(1)
s = Semaphore(0)
summ = 0
nproc = 0

def sumstop(v):
	global summ,nproc
	mutex.acquire()
	summ += v
	nproc += 1
	mutex.release()
	s.acquire()
	summ -= v

	

def sumgo():
	global summ,nproc
	mutex.acquire()
	mem = summ
	for _ in range(nproc):
		s.release()
	nproc = 0
	mutex.release()
	return mem

#Esercizio c.1: Scrivere il monitor multibuf che implementi un buffer limitato (MAX elementi) di oggetti di tipo T che
#implementi le seguenti procedure entry:
#void add(int n, T objexts[]);
#void get(int n, T objects[]);
#La funzione add deve aggiungere al buffer gli n oggetti passati col parametro objects. La funzione get deve predere
#dal buffer in modalità FIFO i primi n elementi presenti nel buffer e copiarli negli elementi del vettore objects.
#Entrambe le funzioni devono attendere che vi siano le condizioni per poter essere completate: che ci siano n elementi
#liberi per la add, che ci siano n elementi nel buffer per la get. Non sono ammesse esecuzioni parziali: mentre attendono
#le rispettive condizioni nessun elemento può essere aggiunto o rimosso dal buffer.
#La definizione del problema C.1 presenta casi di possibile deadlock? quali?

class multibuff(monitor.monitor):
	def __init__(self,):
		super().__init__()
		self.store = []
		self.condadd = monitor.condition(self)
		self.condget = monitor.condition(self)

	@monitor.entry
	def add(self,n,obj):
		if len(self.store) > 0:
			self.condadd.wait()
		for i in range(n):
			self.store.append(obj[i])
		self.condget.signal()
		


	@monitor.entry
	def get(self,n,obj):
		if len(self.store) != n:
			self.condget.wait()
		else:
			for i in range(n):
				obj.append(self.store[i])
			self.condadd.signal()
		return obj
			

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
send_result che lo restituisce al cliente come valore di ritorno della funzione request
'''
class cs(monitor.monitor):
	def __init__(self):
		super().__init__()
		self.requestsNumber = 0  #numero di richieste
		self.data = 0 #dato da trasmettere (suppongo intero)
		self.condition = monitor.condition(self)
		self.servernumber = 0
	
	@monitor.entry
	def get_request(self,servernumber):
		self.servernumber = servernumber
		return self.data

	@monitor.entry
	def request(self,data):
		self.requestsNumber += 1
		self.data = data
		#il cliente si addormenta
		return self.data

	
	@monitor.entry
	def send_result(self,clientnumber,data):
		#sveglia il client
		return 0
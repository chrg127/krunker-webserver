"""
Traccia:
Si immagini di dover realizzare un Web Server in Python per
una azienda ospedaliera. I requisiti del Web Server sono i
seguenti:
    - Il web server deve consentire l’accesso a più utenti in
      contemporanea
    - La pagina iniziale deve consentire di visualizzare la lista
      dei servizi erogati dall’azienda ospedaliera e per ogni
      servizio avere un link di riferimento ad una pagina
      dedicata.
    - L’interruzione da tastiera (o da console) dell’esecuzione
      del web server deve essere opportunamente gestita in
      modo da liberare la risorsa socket.
    - Nella pagina principale dovrà anche essere presente un
      link per il download di un file pdf da parte del browser.
    - Come requisito facoltativo si chiede di autenticare gli
      utenti nella fase iniziale della connessione.
"""

import myserver

if __name__ == "__main__":
    myserver.start_server()


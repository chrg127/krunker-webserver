"""
Traccia:
Si immagini di dover realizzare un Web Server in Python per
una azienda ospedaliera. I requisiti del Web Server sono i
seguenti:
    - Il web server deve consentire l’accesso a più utenti in
      contemporanea *
    - La pagina iniziale deve consentire di visualizzare la lista
      dei servizi erogati dall’azienda ospedaliera e per ogni
      servizio avere un link di riferimento ad una pagina
      dedicata. *
    - L’interruzione da tastiera (o da console) dell’esecuzione
      del web server deve essere opportunamente gestita in
      modo da liberare la risorsa socket. *
    - Nella pagina principale dovrà anche essere presente un
      link per il download di un file pdf da parte del browser *
    - Come requisito facoltativo si chiede di autenticare gli
      utenti nella fase iniziale della connessione. *
"""

import sys
import signal
import socketserver, http.server, cgi

import mysite

# constants
PORT = 8000
GETREQ_FILENAME = "files/requests_get.txt"
POSTREQ_FILENAME = "files/requests_post.txt"
USERDB_FILENAME = "files/users.txt"

# load and parse a key-value textual database
def load_kv(pathname):
    db = {}
    with open(pathname) as f:
        for line in f:
            usr, passw = line.strip().split('=', 1)
            db[usr] = passw
    return db

# used to keep together username and ip address
class User:
    def __init__(self, name, ipaddr):
        self.name = name
        self.ipaddr = ipaddr

# request handler class
class HospistalRequestHandler(http.server.SimpleHTTPRequestHandler):
    user_db = load_kv(USERDB_FILENAME)
    logged_users = {}

    def login_handler(self, content):
        username = content.getvalue("username")
        password = content.getvalue("password")
        if username not in self.user_db or self.user_db[username] != password:
            return mysite.load_page("loginbad.html")
        ipaddr = self.client_address[0]
        if ipaddr not in self.logged_users:
            self.logged_users[ipaddr] = User(username, ipaddr)
        return mysite.load_page("logingood.html")

    post_handlers = {
        "/login.html" : login_handler,
    }

    # creates a dynamic page. assumes pageurl is a valid url.
    def create_dynamic(self, pageurl):
        ip = self.client_address[0]
        username = None
        if ip in self.logged_users:
            username = self.logged_users[ip].name
        mysite.create_page(pageurl, username)

    def do_GET(self):
        with open(GETREQ_FILENAME, "a") as f:
            f.write("GET request\n")
            f.write("Path: " + str(self.path) + '\n')
            f.write("Headers:\n" + str(self.headers))

        if self.path == "/":
            self.path = "/index.html"

        if self.path[1:] in mysite.pagetab:
            self.create_dynamic(self.path[1:])

        http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        with open(POSTREQ_FILENAME, "a") as f:
            f.write("POST request\n")
            f.write("Path: " + str(self.path) + '\n')
            f.write("Headers:\n" + str(self.headers))
        content = cgi.FieldStorage(
            fp = self.rfile,
            headers = self.headers,
            environ = { 'REQUEST_METHOD' : 'POST' }
        )
        handler = self.post_handlers[self.path]
        output = handler(self, content)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(output, "utf-8"))

def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("", PORT), HospistalRequestHandler)
    httpd.daemon_threads = True
    httpd.allow_reuse_address = True

    def sighandler(num, frame):
        print("exiting server (ctrl+c)")
        httpd.server_close()
        sys.exit(0)
    signal.signal(signal.SIGINT, sighandler)

    print("serving at port", PORT)
    try:
        httpd.serve_forever()
    except:
        httpd.server_close()

def test():
    mysite.create_page("index.html", "viroli mirko")

# test()
if __name__ == "__main__":
    main()

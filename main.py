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

class UserInfo:
    def __init__(self, name, password, kr, guns):
        self.name = name
        self.password = password
        self.kr = kr
        self.guns = guns

def load_user_db(pathname):
    def parse_guns(gunstr):
        if gunstr == "":
            return []
        return gunstr.split(',')
    db = {}
    with open(pathname) as f:
        for line in f:
            user, password, kr, gunstr = line.strip().split('=', 4)
            db[user] = UserInfo(user, password, int(kr), parse_guns(gunstr))
    return db

def write_user_db(db, pathname):
    with open(pathname, "w") as out:
        for key in db:
            user = db[key]
            out.write(user.name + '=' + user.password + '=' + str(user.kr) + '=')
            for i in range(0, len(user.guns) - 1):
                out.write(user.guns[i] + ',')
            out.write(user.guns[len(user.guns)-1])
            out.write('\n')

user_db = load_user_db(USERDB_FILENAME)

# used to keep together username and ip address
class User:
    def __init__(self, name, ipaddr):
        self.name = name
        self.ipaddr = ipaddr

logged_users = {}

# request handler class
class HospistalRequestHandler(http.server.SimpleHTTPRequestHandler):

    def login_handler(self, content):
        username = content.getvalue("username")
        password = content.getvalue("password")
        if username not in user_db or user_db[username].password != password:
            return mysite.load_page("loginbad.html")
        ipaddr = self.client_address[0]
        if ipaddr not in logged_users:
            logged_users[ipaddr] = User(username, ipaddr)
        return mysite.load_page("logingood.html")

    def kr_handler(self, content):
        amount = int(content.getvalue("num"))
        user = logged_users[self.client_address[0]]
        user_db[user.name].kr += amount
        print()
        return "hello"

    post_handlers = {
        "/login.html" : login_handler,
        "/getkr.html" : kr_handler,
    }

    # creates a dynamic page. assumes pageurl is a valid url.
    def create_dynamic(self, pageurl):
        ip = self.client_address[0]
        username = None
        if ip in logged_users:
            username = logged_users[ip].name
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
        write_user_db(user_db, USERDB_FILENAME)
        sys.exit(0)
    signal.signal(signal.SIGINT, sighandler)

    print("serving at port", PORT)
    try:
        httpd.serve_forever()
    except:
        httpd.server_close()
        write_user_db(user_db, USERDB_FILENAME)

def test():
    pass

# test()
if __name__ == "__main__":
    main()

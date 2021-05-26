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
from dataclasses import dataclass

import mysite

# Constants.
PORT = 8000
GETREQ_FILENAME = "files/requests_get.txt"
POSTREQ_FILENAME = "files/requests_post.txt"
USERDB_FILENAME = "files/users.txt"

@dataclass
class UserInfo:
    name: str
    password: str
    kr: int
    guns: list

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

class StoreRequestHandler(http.server.SimpleHTTPRequestHandler):

    @dataclass
    class LoggedUser:
        name: str
        ipaddr: str

    logged_users = {}

    # Handler for the POST method in the login page.
    # Checks if the submitted values are valid by searching
    # the database (user_db)
    def login_handler(self, content):
        username = content.getvalue("username")
        password = content.getvalue("password")
        if username not in user_db or user_db[username].password != password:
            return mysite.load_page_cached("loginbad.html")
        ipaddr = self.client_address[0]
        if ipaddr not in self.logged_users:
            self.logged_users[ipaddr] = self.LoggedUser(username, ipaddr)
        return mysite.load_page_cached("logingood.html")

    # Handler for POST function in the "play" page.
    # It simply adds an amount defined by the page to the user.
    # Since this is a login-only page, we don't need to check whether
    # self.client_address is inside logged_users.
    def kr_handler(self, content):
        amount = int(content.getvalue("num"))
        user = self.logged_users[self.client_address[0]]
        user_db[user.name].kr += amount
        return ""

    post_handlers = {
        "/login.html" : login_handler,
        "/getkr.html" : kr_handler,
    }

    # Creates a dynamic page. Assumes pageurl is a valid url.
    def create_dynamic(self, pageurl):
        ip = self.client_address[0]
        username = self.logged_users[ip].name if ip in self.logged_users else None
        return mysite.create_page(pageurl, username)

    # Handler for any GET functions.
    def do_GET(self):
        # Log any GET made.
        with open(GETREQ_FILENAME, "a") as f:
            f.write("GET request\n")
            f.write("Path: " + str(self.path) + '\n')
            f.write("Headers:\n" + str(self.headers))

        # Make sure the user gets redirected to the index page when
        # visiting the root.
        if self.path == "/":
            self.path = "/index.html"

        # Is the page we're visiting a dynamic page?
        if self.path[1:] in mysite.pagetab:
            res = self.create_dynamic(self.path[1:])
            # Also check for privilege - we don't want a guest seeing a user page!
            if not res:
                mysite.copy_page("noaccess.html")
                self.path = "/noaccess.html"

        http.server.SimpleHTTPRequestHandler.do_GET(self)

    # Handler for any POST functions.
    def do_POST(self):
        # Log any POST made.
        with open(POSTREQ_FILENAME, "a") as f:
            f.write("POST request\n")
            f.write("Path: " + str(self.path) + '\n')
            f.write("Headers:\n" + str(self.headers))

        # Parse content using cgi.
        content = cgi.FieldStorage(
            fp = self.rfile,
            headers = self.headers,
            environ = { 'REQUEST_METHOD' : 'POST' }
        )

        # Direct handling of the content to an appropiately defined function.
        # This is done using a function table.
        handler = self.post_handlers[self.path]

        # Send back whatever the handler returned.
        output = handler(self, content)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(output, "utf-8"))

def main():
    # Use ThreadingTCPServer to handle multiple connections.
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("", PORT), StoreRequestHandler)
    httpd.daemon_threads = True
    httpd.allow_reuse_address = True

    # Handles <CTRL-C>
    def sighandler(num, frame):
        print("exiting server (ctrl+c)")
        httpd.server_close()
        write_user_db(user_db, USERDB_FILENAME)
        sys.exit(0)
    signal.signal(signal.SIGINT, sighandler)

    print("serving at port:", PORT)
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

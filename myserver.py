import sys
import signal
import socketserver, http.server, cgi
from dataclasses import dataclass

import mysite
import mydatabase

# Constants.
PORT = 8000
GETREQ_FILENAME = "files/requests_get.txt"
POSTREQ_FILENAME = "files/requests_post.txt"
USERDB_FILENAME = "files/users.txt"

user_db = mydatabase.UserDatabase(USERDB_FILENAME)

class StoreRequestHandler(http.server.SimpleHTTPRequestHandler):

    @dataclass
    class LoggedUser:
        name: str
        ipaddr: str

    logged_users = {}

    # Handler for the POST method in the login page. Checks if the submitted values
    # are valid by searching the database (user_db).
    def login_handler(self, content):
        username = content.getvalue("username")
        password = content.getvalue("password")
        if username not in user_db or user_db[username].password != password:
            return mysite.load_page_cached("loginbad.html")
        ipaddr = self.client_address[0]
        if ipaddr not in self.logged_users:
            self.logged_users[ipaddr] = self.LoggedUser(username, ipaddr)
        return mysite.load_page_cached("logingood.html")

    # Handler for POST function in the "play" page. It simply adds an amount defined by the page to the user.
    # Since this is a login-only page, we don't need to check whether self.client_address is inside logged_users.
    def kr_handler(self, content):
        amount = int(content.getvalue("num"))
        user = self.logged_users[self.client_address[0]]
        user_db[user.name].kr += amount
        return ""

    def shop_handler(self, content):
        msg_nokr = """
        <h2>Acquisto non effettuato.</h2>
        <p>I tuoi KR non sono abbastanza!</p>
        <p>I tuoi KR: {}</p>
        <p>Costo dell'arma: {}</p>"""
        msg_ok = """
        <h2>Acquisto effettuato.</h2>
        <p>Nelle tue "stats" potrai vedere la tua nuova arma.</p>"""
        msg_gotalready = """
        <h2>Acquisto non effettuato</h2>
        <p>Sembra che tu abbia già quest'arma.</p>"""
        gunid    = int(content.getvalue("gun"))
        guninfo  = mydatabase.guntab[gunid]
        user     = self.logged_users[self.client_address[0]]
        userinfo = user_db[user.name]
        if userinfo.kr < guninfo.cost:
            return msg_nokr.format(userinfo.kr, guninfo.cost) + mysite.load_page_cached("shopreply.html")
        elif gunid in userinfo.guns:
            return msg_gotalready + mysite.load_page_cached("shopreply.html")
        else:
            userinfo.kr -= guninfo.cost
            userinfo.guns.append(gunid)
            user_db.write()
            return msg_ok + mysite.load_page_cached("shopreply.html")

    def logout_handler(self, content):
        ipaddr = self.client_address[0]
        del self.logged_users[ipaddr]
        return mysite.load_page_cached("logoutreply.html")

    def spinner_handler(self, content):
        user     = self.logged_users[self.client_address[0]]
        userinfo = user_db[user.name]
        if userinfo.freespin:
            return "Free spin fallito. Hai gia fatto il tuo free spin!<br>" + mysite.load_page_cached("spinreply.html")
        gunid, gun = mydatabase.random_gun(userinfo.guns)
        if gunid == -1:
            return "Free spin fallito. Hai gia tutte le armi!<br>" + mysite.load_page_cached("spinreply.html")
        userinfo.guns.append(gunid)
        userinfo.freespin = True
        msg_ok = """Hai trovato la {}!<br>Rarita: {}<br><img src="{}" alt=gunpic>""".format(gun.name, gun.rank, gun.image_path)
        return msg_ok + mysite.load_page_cached("spinreply.html")

    post_handlers = {
        "/login.html" : login_handler,
        "/getkr.html" : kr_handler,
        "/shop.html"  : shop_handler,
        "/logout.html" : logout_handler,
        "/spinner.html" : spinner_handler,
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
                self.path = "/noaccess.html"

        http.server.SimpleHTTPRequestHandler.do_GET(self)

    # Handler for any POST functions.
    def do_POST(self):
        # Log any POST made.
        with open(POSTREQ_FILENAME, "a") as f:
            f.write("POST request\n")
            f.write("Path: " + str(self.path) + '\n')
            f.write("Headers:\n" + str(self.headers))

        # Parse content and send it to the handler function for the page.
        content = cgi.FieldStorage(
            fp = self.rfile,
            headers = self.headers,
            environ = { 'REQUEST_METHOD' : 'POST' }
        )
        handler = self.post_handlers[self.path]
        output = handler(self, content)

        # Send back whatever the handler returned.
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes(output, "utf-8"))

def start_server():
    # Use ThreadingTCPServer to handle multiple connections.
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("", PORT), StoreRequestHandler)
    httpd.daemon_threads = True
    httpd.allow_reuse_address = True

    # Handles <CTRL-C>
    def sighandler(num, frame):
        print("exiting server (ctrl+c)")
        httpd.server_close()
        user_db.write()
        sys.exit(0)
    signal.signal(signal.SIGINT, sighandler)

    def make_gun_table():
        res = "<table>"
        for i in range(0, len(mydatabase.guntab)):
            gun = mydatabase.guntab[i]
            res += """
    <tr>
        <td>{}</td>
        <td><img src="{}" alt=gunpic></td>
        <td>Costo: {}</td>
        <td>
            <form action="" method="post">
                <button type="submit" name="gun" value="{}">Compra</button>
            </form>
        </td>
    </tr>
            """.format(gun.name, gun.image_path, gun.cost, i)
        res += "</table>"
        return res

    def get_stats(user):
        if user not in user_db:
            return "[invalid]"
        userinfo = user_db[user]
        res = "KR: {}\n<br>\nArmi:\n<br>\n<table>\n".format(userinfo.kr)
        if len(userinfo.guns) == 0:
            return res + r"<br><p>Nessuna arma ancora comprata</p>"
        for gun in userinfo.guns:
            guninfo = mydatabase.guntab[gun]
            res += """
        <tr>
            <td>{}</td>
            <td><img src="{}" alt="gunpic"></td>
        </tr>
            """.format(guninfo.name, guninfo.image_path)
        res += "</table>"
        return res

    mysite.page_add_content("shop.html", mysite.PageAccess.USER_GUEST, make_gun_table())
    mysite.page_on_GET("stats.html", get_stats)
    mysite.copy_page("noaccess.html")

    print("serving at port:", PORT)
    try:
        httpd.serve_forever()
    except:
        httpd.server_close()
        user_db.write()

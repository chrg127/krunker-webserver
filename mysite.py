import enum

class PageAccess(enum.Enum):
    USER_ONLY   = 1
    GUEST_ONLY  = 2
    USER_GUEST  = 3

class Page:
    def __init__(self, name, filename, filename_user, access):
        self.name = name
        self.filename = filename
        self.filename_user = filename_user
        self.access = access
        with open(filename) as f:
            self.contents = f.read()
        if filename_user != None:
            with open(filename_user) as f:
                self.contents_user = f.read()
        else:
            self.contents_user = None

PAGE_DIR = "templates/"
pagetab = {
    "index.html"    : Page("Home",      PAGE_DIR + "index.html",    PAGE_DIR + "index_user.html", PageAccess.USER_GUEST),
    "about.html"    : Page("About",     PAGE_DIR + "about.html",    None,                         PageAccess.USER_GUEST),
    "login.html"    : Page("Login",     PAGE_DIR + "login.html",    None,                         PageAccess.GUEST_ONLY),
    "getkr.html"    : Page("Play",      PAGE_DIR + "getkr.html",    None,                         PageAccess.USER_ONLY),
    "buy.html"      : Page("Buy Guns",  PAGE_DIR + "buy.html",      None,                         PageAccess.USER_ONLY),
    "stats.html"    : Page("See stats", PAGE_DIR + "stats.html",    None,                         PageAccess.USER_ONLY),
}

def load_page(url):
    with open(PAGE_DIR + url, "r") as f:
        return f.read()

HEAD_TEMPLATE = load_page("head.html")

def make_div(divclass, content):
    return "<div class=\"" + divclass + "\">\n" + content + "\n</div>"

def make_sidebar(access):
    sidebar = ""
    for url in pagetab:
        page = pagetab[url]
        if page.access.value & access.value:
            sidebar += "<a href=\"/" + url + "\">" + pagetab[url].name + "</a>\n"
    return sidebar

# create a dynamic page.
#   url: name of the dynamic page, should end with .html.
#   username: name of the user that is accessing, or None for a "guest" user.
def create_page(url, username):
    def logged_user_message(username):
        if username == None:
            return ""
        return "<footer>Logged in as " + username + "</footer>"

    def create_page_content(page, username):
        if username == None:
            return page.contents + "<br>"
        elif page.filename_user == None:
            return page.contents + "<br>"
        else:
            return page.contents_user + "<br>"

    if url not in pagetab:
        return
    page = pagetab[url]
    access = PageAccess.GUEST_ONLY if username == None else PageAccess.USER_ONLY
    page_content = create_page_content(page, username)
    with open(url, "w") as out:
        def wr(s): out.write(s + '\n')

        wr("<html>")
        wr("    </head>")
        wr("    <title>Krunker Store: " + page.name + "</title>")
        wr(HEAD_TEMPLATE)
        wr("    </head>")
        wr("    <body>")
        wr(make_div("sidenav", make_sidebar(access)))
        wr(make_div("main", page_content))
        wr(make_div("foot", logged_user_message(username)))
        wr("    </body>")
        wr("</html>")

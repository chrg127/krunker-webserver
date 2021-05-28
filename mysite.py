import enum
from dataclasses import dataclass
import shutil

import mydatabase

class PageAccess(enum.Enum):
    USER_ONLY   = 1
    GUEST_ONLY  = 2
    USER_GUEST  = 3

class Page:
    def __init__(self, name, filename_guest, filename_user, access):
        def get_content(pathname):
            if pathname == None:
                return None
            with open(pathname) as f:
                return f.read()
        self.name = name
        self.filename_guest = filename_guest
        self.filename_user = filename_user
        self.access = access
        self.contents_guest = get_content(filename_guest)
        self.contents_user  = get_content(filename_user)
        self.load_fn = None

    def get_contents(self, access):
        if access == PageAccess.USER_ONLY:
            return self.contents_user
        elif access == PageAccess.GUEST_ONLY:
            return self.contents_guest
        else:
            print("Wrong access passed")
            return ""

PAGE_DIR = "templates/"
pagetab = {
    "index.html"    : Page("Home",      PAGE_DIR + "index.html",    PAGE_DIR + "index_user.html", PageAccess.USER_GUEST),
    "about.html"    : Page("About",     PAGE_DIR + "about.html",    PAGE_DIR + "about.html",      PageAccess.USER_GUEST),
    "login.html"    : Page("Login",     PAGE_DIR + "login.html",    None,                         PageAccess.GUEST_ONLY),
    "getkr.html"    : Page("Play",      None,                       PAGE_DIR + "getkr.html",      PageAccess.USER_ONLY),
    "shop.html"     : Page("Shop",      None,                       PAGE_DIR + "shop.html",       PageAccess.USER_ONLY),
    "stats.html"    : Page("See stats", None,                       PAGE_DIR + "stats.html",      PageAccess.USER_ONLY),
    "logout.html"   : Page("Logout",    None,                       PAGE_DIR + "logout.html",     PageAccess.USER_ONLY),
}

def load_page_cached(url):
    global cache
    cache = {}
    if url not in cache:
        with open(PAGE_DIR + url, "r") as f:
            cache[url] = f.read()
    return cache[url]

def copy_page(url):
    shutil.copyfile(PAGE_DIR + url, url)

HEAD_TEMPLATE = load_page_cached("head.html")

def make_div(divclass, content):
    return "<div class=\"" + divclass + "\">\n" + content + "\n</div>"

def make_sidebar(access):
    sidebar = ""
    for url in pagetab:
        page = pagetab[url]
        if page.access.value & access.value:
            sidebar += "<a href=\"/" + url + "\">" + pagetab[url].name + "</a>\n"
    return sidebar

# Create a dynamic page.
#   url: name of the dynamic page, should end with .html.
#   username: name of the user that is accessing, or None for a "guest" user.
# If the user doesn't have access to the page (for example, a guest visiting a
# page only visitable by a user), then the function returns false.
def create_page(url, username):
    if url not in pagetab:
        return False
    access = PageAccess.GUEST_ONLY if username == None else PageAccess.USER_ONLY
    page = pagetab[url]
    page_content = page.get_contents(access)
    if page_content == None:
        return False

    with open(url, "w") as out:
        text = """
<html>
    </head>
        <title>Krunker Store: {}</title>
        {}
    </head>
    <body>
        <div class="sidenav">
            {}
        </div>
        <div class="main">
            {}
            {}
        </div>
        <div class="foot">
            {}
        </div>
    </body>
</html>""".format(
        page.name, HEAD_TEMPLATE,
        make_sidebar(access),
        page_content,
        page.load_fn(username) if page.load_fn != None else "",
        "<footer>Logged in as {}</footer>".format(username) if username != None else "")
        out.write(text)

    return True

def page_add_content(page, access, content):
    try:
        if access == PageAccess.USER_ONLY or access == PageAccess.USER_GUEST:
            pagetab[page].contents_user += content
        if access == PageAccess.GUEST_ONLY or access == PageAccess.USER_GUEST:
            pagetab[page].contents_guest += content
    except:
        pass

def page_on_GET(page, fn):
    try:
        pagetab[page].load_fn = fn
    except:
        pass

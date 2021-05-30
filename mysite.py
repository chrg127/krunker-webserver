import enum
import shutil

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
    "getkr.html"    : Page("Gioca",     None,                       PAGE_DIR + "getkr.html",      PageAccess.USER_ONLY),
    "shop.html"     : Page("Shop",      None,                       PAGE_DIR + "shop.html",       PageAccess.USER_ONLY),
    "stats.html"    : Page("Statistiche", None,                     PAGE_DIR + "stats.html",      PageAccess.USER_ONLY),
    "logout.html"   : Page("Logout",    None,                       PAGE_DIR + "logout.html",     PageAccess.USER_ONLY),
}

# Load a page's contents. On the first call the contents are fetched from disk,
# afterwards they will stay in a cache (and therefore can be easily retrieved.
def load_page_cached(path):
    global cache
    cache = {}
    if path not in cache:
        with open(PAGE_DIR + path, "r") as f:
            cache[path] = f.read()
    return cache[path]

def copy_page(path):
    shutil.copyfile(PAGE_DIR + path, path)


_HEAD_TEMPLATE = load_page_cached("head.html")

# Create a dynamic page.
#   pathname: name of the dynamic page, should end with .html.
#   username: name of the user that is accessing, or None for a "guest" user.
# If the user doesn't have access to the page (for example, a guest visiting a
# page only visitable by a user), then the function returns false.
def create_page(pathname, username):
    def make_sidebar(access, username):
        sidebar = ""
        for path in pagetab:
            page = pagetab[path]
            if page.access.value & access.value:
                sidebar += """<a href="/{}">{}</a>\n""".format(path, page.name)
        sidebar += """<a href="/files/info.pdf">Info (PDF)</a>"""
        sidebar += "<p>{}</p>\n".format("Logged as " + username if username != None else "")
        return sidebar

    if pathname not in pagetab:
        return False
    access = PageAccess.GUEST_ONLY if username == None else PageAccess.USER_ONLY
    page = pagetab[pathname]
    page_content = page.get_contents(access)
    if page_content == None:
        return False

    with open(pathname, "w") as out:
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
    </body>
</html>""".format(
        page.name, _HEAD_TEMPLATE,
        make_sidebar(access, username),
        page_content,
        page.load_fn(username) if page.load_fn != None else "")
        out.write(text)

    return True

# Adds content to a page after it is loaded from the file. The content
# is not written to file.
def page_add_content(page, access, content):
    try:
        if access == PageAccess.USER_ONLY or access == PageAccess.USER_GUEST:
            pagetab[page].contents_user += content
        if access == PageAccess.GUEST_ONLY or access == PageAccess.USER_GUEST:
            pagetab[page].contents_guest += content
    except:
        pass

# Run a function "fn" when GETting a page.
def page_on_GET(page, fn):
    try:
        pagetab[page].load_fn = fn
    except:
        pass


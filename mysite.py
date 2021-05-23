import enum

class PageAccess(enum.Enum):
    USER_ONLY   = 1
    GUEST_ONLY  = 2
    USER_GUEST  = 3

class Page:
    def __init__(self, name, filename, access):
        self.name = name
        self.filename = filename
        self.access = access
        with open(filename) as f:
            self.contents = f.read()

HEAD_TEMPLATE = """
    <meta charset="utf-8" name="viewport" content="width=device-width, initial-scale=1">
    <style>
        .sidenav {
            height: 100%;
            width: 240px;
            position: fixed;
            z-index: 1;
            top: 0;
            left: 0;
            background-color: #111;
            overflow-x: hidden;
            padding-top: 20px;
        }

        .sidenav a {
            padding: 6px 8px 6px 16px;
            text-decoration: none;
            font-size: 25px;
            color: #818181;
            display: block;
        }

        .sidenav a:hover {
            color: #f1f1f1;
        }

        .main {
            margin-left: 240px;
            padding: 0px 10px;
        }
    </style>
"""
PAGE_DIR = "templates/"
pagetab = {
    "index.html"    : Page("Home",      PAGE_DIR + "index.html",    PageAccess.USER_GUEST),
    "about.html"    : Page("About",     PAGE_DIR + "about.html",    PageAccess.USER_GUEST),
    "contact.html"  : Page("Contact",   PAGE_DIR + "contact.html",  PageAccess.USER_GUEST),
    "form.html"     : Page("Form",      PAGE_DIR + "form.html",     PageAccess.USER_GUEST),
    "login.html"    : Page("Login",     PAGE_DIR + "login.html",    PageAccess.GUEST_ONLY),
}

def make_div(divclass, content):
    return "<div class=\"" + divclass + "\">\n" + content + "\n</div>\n"

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
    if url not in pagetab:
        return
    access = PageAccess.GUEST_ONLY if username == None else PageAccess.USER_ONLY
    page_content = pagetab[url].contents + "<br>"
    if username != None:
        page_content += "Logged in as " + username + "<br>"
    with open(url, "w") as out:
        out.write("""<html>
                        <head>""")
        out.write(HEAD_TEMPLATE)
        out.write("""   </head>
                        <body>""")
        out.write(make_div("sidenav", make_sidebar(access)))
        out.write(make_div("main", page_content))
        out.write("""   </body>
                    </html>""")

def load_page(url):
    with open(PAGE_DIR + url, "r") as f:
        return f.read()

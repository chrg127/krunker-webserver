from dataclasses import dataclass
import enum
import random

@dataclass
class UserInfo:
    name: str
    password: str
    kr: int
    freespin: bool
    guns: list

class Rank(enum.Enum):
    COMMON = 0
    RARE = 1
    EPIC = 2
    LEGEND = 3

@dataclass
class Gun:
    name: str
    image_path: str
    cost: int
    rank: Rank

IMAGEDIR = "images/"
guntab = [
    Gun("Akimbo Uzi",     IMAGEDIR + "akimbo.png",        50,       Rank.COMMON),
    Gun("Knife",          IMAGEDIR + "knife.png",         25,       Rank.COMMON),
    Gun("Machine Gun",    IMAGEDIR + "machinegun.png",    100,      Rank.COMMON),
    Gun("Pistol",         IMAGEDIR + "pistol.png",        10000,    Rank.LEGEND),
    Gun("Revolver",       IMAGEDIR + "revolver.png",      150,      Rank.COMMON),
    Gun("Assault Rifle",  IMAGEDIR + "rifle.png",         200,      Rank.COMMON),
    Gun("Shotgun",        IMAGEDIR + "shotgun.png",       300,      Rank.COMMON),
    Gun("Sniper Rifle",   IMAGEDIR + "sniper.png",        500,      Rank.COMMON),
]

class UserDatabase(dict):
    def __init__(self, pathname):
        self.pathname = pathname
        def parse_guns(gunstr):
            if gunstr == "":
                return []
            return [int(gun_id) for gun_id in gunstr.split(',')]
        def parse_bool(s): return False if s == "False" else True
        with open(pathname) as f:
            for line in f:
                user, password, kr, spin, gunstr = line.strip().split('=', 4)
                userinfo = UserInfo(user, password, int(kr), parse_bool(spin), parse_guns(gunstr))
                print(userinfo)
                self.__setitem__(user, userinfo)

    def write(self):
        with open(self.pathname, "w") as out:
            for key in self.__iter__():
                user = self.__getitem__(key)
                out.write(user.name + '=' + user.password + '=' + str(user.kr) + '=' + str(user.freespin) + '=')
                if len(user.guns) != 0:
                    for i in range(0, len(user.guns) - 1):
                        out.write(str(user.guns[i]) + ',')
                    out.write(str(user.guns[len(user.guns)-1]))
                out.write('\n')

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)

def random_gun(blacklist):
    valid_ids = list(set(range(0, len(guntab))) - set(blacklist))
    if len(valid_ids) == 0:
        return -1, None
    gunid = valid_ids[random.randrange(len(valid_ids))]
    return gunid, guntab[gunid]



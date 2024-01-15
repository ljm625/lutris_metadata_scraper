import os
import sqlite3


class Lutris(object):

    def __init__(self,update_title=False,db_path=None):
        self.os_user = os.getlogin()
        self.update_title = update_title
        self.game_list = []
        self.conn = None
        self.cover_art_folder = None
        self.banner_art_folder = None

        if db_path:
            self.db_path = db_path
        else:
            if os.path.isdir(f"/home/{self.os_user}/.local/share/lutris"):
                self.db_path=f"/home/{self.os_user}/.local/share/lutris/pga.db"
                self.cover_art_folder = f"/home/{self.os_user}/.cache/lutris/coverart"
                self.banner_art_folder = f"/home/{self.os_user}/.cache/lutris/banners"
            elif os.path.isdir(f"/home/{self.os_user}/.var/app/net.lutris.Lutris/data/lutris"):
                self.db_path=f"/home/{self.os_user}/.var/app/net.lutris.Lutris/data/lutris/pga.db"
                self.cover_art_folder = f"/home/{self.os_user}/.var/app/net.lutris.Lutris/cache/lutris/coverart"
                self.banner_art_folder = f"/home/{self.os_user}/.var/app/net.lutris.Lutris/cache/lutris/banners"

        self.db_get_game_list()

    def db_get_game_list(self):
        self.conn = sqlite3.connect(self.db_path)
        c = self.conn.execute('SELECT id,name,slug FROM games WHERE installed=1')
        games = c.fetchall()
        for entry in games:
            title = entry[0]
            print(title)
            self.game_list.append({"id":entry[0],"title":entry[1],"slug":entry[2]})

    def get_title_list(self):
        return self.game_list

    def update_game_entry(self,id,title,cover_art,banner_art):
        # Just trying
        if self.update_title:
            self.conn.execute(f"UPDATE games SET name ='{title}' WHERE id={id}")
            self.conn.commit()
        # try:
        #     os.mkdir(title)
        # except Exception as e:
        #     pass
        slug = None
        for game in self.game_list:
            if game["id"]==id:
                slug = game["slug"]
        with open(f"{self.cover_art_folder}/{slug}.jpg","wb") as file:
            file.write(cover_art)
        with open(f"{self.banner_art_folder}/{slug}.jpg","wb") as file:
            file.write(banner_art)



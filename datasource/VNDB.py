import httpx


class VNDB(object):

    def __init__(self,prefer_languages):
        self.name = "VNDB"
        self.endpoint="https://api.vndb.org/kana/vn"
        self.prefer_languages = prefer_languages
        self.data = {}
        pass


    async def __download_image(self,url):
        chunks = b""
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', url) as response:
                async for chunk in response.aiter_bytes():
                    chunks += chunk
        return chunks

    def format_data(self,data):
        self.data = {}
        for item in data["results"]:
            self.data[item["title"]]=item

    async def query(self,keyword):
        query_body = {
          "filters": ["search", "=", keyword],
          "fields": "id, title, image.url, description, titles.title, titles.lang, released, screenshots.url"
        }
        headers = {
            "Content-Type": "application/json"
        }
        resp = None
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.endpoint,json=query_body,headers=headers)
        if resp and resp.status_code == 200:
            data = resp.json()
            self.format_data(data)
            return True
        else:
            print("Call API failed!")
            print(resp.status_code)
            print(resp.content)
            return None

    def get_titles(self):
        return list(self.data.keys())

    def get_prefer_title(self,title):
        prefer_title = title
        if self.data.get(title):
            data = self.data[title]
            alt_title = {}
            if data.get("titles"):
                for alt in data["titles"]:
                    alt_title[alt["lang"]]=alt["title"]
            for lang in self.prefer_languages:
                if alt_title.get(lang):
                    prefer_title = alt_title[lang]
                    break
        return prefer_title





    async def get_description(self,title):
        if self.data.get(title):
            data = self.data[title]
            desc = ""
            if data.get("titles"):
                for alt_title in data["titles"]:
                    desc = desc+ "{} {}\n".format(alt_title["title"],alt_title["lang"])
            if data.get("released"):
                desc = desc+"Release Date: {}\n".format(data["released"])
            if data.get("description"):
                desc = desc + data["description"]
            return desc
        else:
            return ""

    async def get_cover_image(self,title):
        if self.data.get(title) and self.data.get(title).get("image"):
            url = self.data[title]["image"]["url"]
            return await self.__download_image(url)
        else:
            return None

    def get_screenshot_count(self,title):
        if self.data.get(title) and self.data.get(title).get("screenshots"):
            return len(self.data.get(title).get("screenshots"))
        else:
            return 0

    async def get_screenshot(self,title,index):
        if self.data.get(title) and self.data.get(title).get("screenshots"):
            screenshots = self.data.get(title).get("screenshots")
            if 0 <= index < len(screenshots):
                screenshot = screenshots[index]["url"]
                return await self.__download_image(screenshot)
        else:
            return None







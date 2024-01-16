import httpx
from bs4 import BeautifulSoup


class DLSite(object):

    def __init__(self,prefer_languages,region="ja_JP"):
        self.endpoint="https://api.vndb.org/kana/vn"
        self.search_endpoint="https://www.dlsite.com/pro/fsr/=/language/jp/sex_category/male/keyword/{}/work_category%5B0%5D/doujin/work_category%5B1%5D/pc/order/trend/options_and_or/and/from/topsearch.more"
        self.prefer_languages = prefer_languages
        self.region = region
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
        soup = BeautifulSoup(data, 'html.parser')
        # print(soup.prettify())
        results = soup.find_all(id="search_result_list")[1].find_all("dt")
        self.data = {}
        for result in results:
            link = result.a["href"]
            title = result.img["alt"]
            img_url = result.img["src"]
            self.data[title]={"title":title,"link":link,"image":f"https:{img_url}"}
            print(f"{title} {link} {img_url}")
        # for item in data["results"]:
        #     self.data[item["title"]]=item

    async def query(self,keyword):
        query_params = {
            "locale": self.region
        }
        headers = {
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = None
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.search_endpoint.format(keyword),params=query_params,headers=headers)
        if resp and resp.status_code == 200:
            data = resp.text
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





    def get_description(self,title):
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
            url = self.data[title]["image"]
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







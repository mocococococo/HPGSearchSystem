import requests
import json
import logging


class HotPepper:
    """Recruit APIを使用して飲食店情報を取得するクラス"""
    Area :str
    Budget: str
    Genre: str
    RestaurantNameList: list[str]
        
    def __init__(self):
        self.APIKEY = getAPI("RecruitAPIKey")
        self.gourmetRequest = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/?key={}".format(self.APIKEY)
        self.AreaRequest = "http://webservice.recruit.co.jp/hotpepper/large_area/v1/?key={}&keyword={}&format=json".format(self.APIKEY, "{}")
        self.BudgetRequest = "http://webservice.recruit.co.jp/hotpepper/budget/v1/?key={}&format=json".format(self.APIKEY)
        self.GenreRequest = "http://webservice.recruit.co.jp/hotpepper/genre/v1/?key={}&keyword={}&format=json".format(self.APIKEY, "{}")
        self.AREA = "&large_area={}"
        self.BUDGET = "&budget={}"
        self.GENRE = "&genre={}"
        self.END = "&order=4&format=json"
        self.Area = ""
        self.Genre = ""
        self.Budget = ""
        self.RestaurantNameList = []
        
    def getArea_code(self, area: str) -> str:
        """エリアのコードを取得する関数"""
        print(f"requesting area: {self.AreaRequest.format(area)}")
        response = requests.get(self.AreaRequest.format(area))
        if response.status_code == 200:
            response = response.json()
            print(response)
            code = response["results"]["large_area"][0]["code"]
            print(f"Area code for {area}: {code}")
            return code
        else:
            logging.error(f"Error fetching area data: {response.status_code}")
            return ""
        

    def getBudget_json(self) -> dict:
        """予算のコードを取得する関数"""
        print(f"requesting budget: {self.BudgetRequest}")
        response = requests.get(self.BudgetRequest)
        if response.status_code == 200:
            response = response.json()
            budget_list = response["results"]["budget"]
            print(f"Budget list: {budget_list}")
            return budget_list
        else:
            logging.error(f"Error fetching budget data: {response.status_code}")
            return {}
        
        
    def getGenre_code(self, genre_list: list[str]) -> list[str]:
        """ジャンルのコードを取得する関数"""
        genre_codes = []
        for genre in genre_list:
            print(f"requesting genre: {self.GenreRequest.format(genre)}")
            response = requests.get(self.GenreRequest.format(genre))
            if response.status_code == 200:
                response = response.json()
                print(response)
                for code in response["results"]["genre"]:
                    if code["code"] not in genre_codes:
                        genre_codes.append(code["code"])
            else:
                logging.error(f"Error fetching genre data for {genre}: {response.status_code}")
        print(f"Genre codes: {genre_codes}")
        if not genre_codes:
            logging.warning("No genre codes found.")
            return []

        return genre_codes
    
    
    def getRestaurantInfo(self) -> int:
        self.RestaurantNameList = []
        gourmetRequest = self.gourmetRequest + self.AREA.format(self.Area) + self.BUDGET.format(self.Budget) + self.GENRE.format(self.Genre)
        gourmetRequest += self.END
        print(f"requesting gourmet: {gourmetRequest}")
        response = requests.get(gourmetRequest)
        if response.status_code == 200:
            response = response.json()
            print(f"Response: {response}")
            if "results" in response and "shop" in response["results"]:
                NumberOfShops = int(response["results"]["results_returned"])
                print(f"Number of shops found: {NumberOfShops}")
                for shop in response["results"]["shop"]:
                    self.RestaurantNameList.append(shop["name"])
                print(f"Restaurant names: {self.RestaurantNameList}")
                return NumberOfShops
            else:
                logging.warning("No shops found in the response.")
                return {}
        else:
            logging.error(f"Error fetching gourmet data: {response.status_code}")
            return {}
        
        
    def setArea(self, area_list: list[str]) -> int:
        """エリアコードをURLパラメータ形式に変換する関数"""
        self.Area = ""
        area_codes = []
        print(f"Area list: {area_list}")
        for area in area_list:
            print("area:", area)
            area_code = self.getArea_code(area)
            if area_code:
                area_codes.append(area_code)
        if area_codes is None or len(area_codes) == 0:
            self.Area = ""
            return 0
        for i in range(min(len(area_codes)-1, 2)):
            self.Area += area_codes[i] + ","
        self.Area += area_codes[-1]
        print(f"Area code set to: {self.Area}")
        return len(area_codes)
        
    def setBudget(self, budget: int) -> None:
        """予算のコードを取得する関数"""
        self.Budget = ""
        if budget is None or budget <= 0:
            self.Budget = ""
            return
        with open("BudgetList.json", "r", encoding="utf-8") as f:
            budget_list = json.load(f)["budget"]
        for budget_info in budget_list:
            if budget_info["min"] <= budget <= budget_info["max"]:
                print(f"Budget code for {budget}: {budget_info['code']}")
                self.Budget = budget_info["code"]
                return
        logging.warning(f"No budget code found for {budget}.")
        return
    
    def setGenre(self, genre_list: list[str]) -> int:
        """ジャンルコードをURLパラメータ形式に変換する関数"""
        self.Genre = ""
        genre_codes = self.getGenre_code(genre_list)
        if genre_codes is None or len(genre_codes) == 0:
            self.Genre = ""
            return 0
        for i in range(min(len(genre_codes)-1, 1)):
            self.Genre += genre_codes[i] + ","
        self.Genre += genre_codes[-1]
        print(f"Genre code set to: {self.Genre}")
        return len(genre_codes)

    
def getAPI(key: str) -> str:
    """APIキーを取得する関数"""
    filename = "apiKey.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data[key]
    
    
if __name__ == "__main__":
    # テスト用のコード
    recruit = HotPepper()
    area_list = ["東京"]
    genre_list = ["ラーメン"]
    budget = 1000
    recruit.setArea(area_list)
    recruit.setBudget(budget)
    recruit.setGenre(genre_list)
    recruit.getRestaurantInfo()
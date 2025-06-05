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
        self.LargeAreaRequest = "http://webservice.recruit.co.jp/hotpepper/large_area/v1/?key={}&keyword={}&format=json".format(self.APIKEY, "{}")
        self.MiddleAreaRequest = "http://webservice.recruit.co.jp/hotpepper/middle_area/v1/?key={}&keyword={}&format=json".format(self.APIKEY, "{}")
        self.SmallAreaRequest = "http://webservice.recruit.co.jp/hotpepper/small_area/v1/?key={}&keyword={}&format=json".format(self.APIKEY, "{}")
        self.BudgetRequest = "http://webservice.recruit.co.jp/hotpepper/budget/v1/?key={}&format=json".format(self.APIKEY)
        self.GenreRequest = "http://webservice.recruit.co.jp/hotpepper/genre/v1/?key={}&keyword={}&format=json".format(self.APIKEY, "{}")
        self.LARGE_AREA = "&large_area={}"
        self.MIDDLE_AREA = "&middle_area={}"
        self.SMALL_AREA = "&small_area={}"
        self.BUDGET = "&budget={}"
        self.GENRE = "&genre={}"
        self.END = "&order=4&format=json"
        self.LargeArea = ""
        self.MiddleArea = ""
        self.SmallArea = ""
        self.Genre = ""
        self.Budget = ""
        self.RestaurantNameList = []
        
    def getArea_code(self, area: str) -> str:
        """エリアのコードを取得する関数"""
        print(f"requesting area: {self.LargeAreaRequest.format(area)}")
        print(f"requesting area: {self.MiddleAreaRequest.format(area)}")
        print(f"requesting area: {self.SmallAreaRequest.format(area)}")
        large_response = requests.get(self.LargeAreaRequest.format(area))
        middle_response = requests.get(self.MiddleAreaRequest.format(area))
        small_response = requests.get(self.SmallAreaRequest.format(area))
        if large_response.status_code == 200:
            large_response = large_response.json()
            print(large_response)
            if int(large_response["results"]["results_returned"]) > 0:
                code = large_response["results"]["large_area"][0]["code"]
                print(f"Area code for {area}: {code}")
                return "L", code
        if middle_response.status_code == 200:
            middle_response = middle_response.json()
            print(middle_response)
            if int(middle_response["results"]["results_returned"]) > 0:
                code = middle_response["results"]["middle_area"][0]["code"]
                print(f"Area code for {area}: {code}")
                return "M", code
        if small_response.status_code == 200:
            small_response = small_response.json()
            print(small_response)
            if int(small_response["results"]["results_returned"]) > 0:
                code = small_response["results"]["small_area"][0]["code"]
                print(f"Area code for {area}: {code}")
                return "S", code
        return "", ""
        

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
        print(f"{self.LargeArea}, {self.MiddleArea}, {self.SmallArea}, {self.Budget}, {self.Genre}")
        gourmetRequest = self.gourmetRequest
        if self.LargeArea != "":
            gourmetRequest += self.LARGE_AREA.format(self.LargeArea)
        elif self.MiddleArea != "":
            gourmetRequest += self.MIDDLE_AREA.format(self.MiddleArea)
        elif self.SmallArea != "":
            gourmetRequest += self.SMALL_AREA.format(self.SmallArea)
        gourmetRequest += self.BUDGET.format(self.Budget) + self.GENRE.format(self.Genre) + self.END
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
        self.LargeArea = ""
        self.MiddleArea = ""
        self.SmallArea = ""
        area_codes = []
        print(f"Area list: {area_list}")
        for area in area_list:
            print("area:", area)
            type, area_code = self.getArea_code(area)
            if area_code != "":
                area_codes.append(area_code)
                if type == "L":
                    self.LargeArea += area_code + ","
                elif type == "M":
                    self.MiddleArea += area_code + ","
                elif type == "S":
                    self.SmallArea += area_code + ","
        self.LargeArea = self.LargeArea.rstrip(',')
        self.MiddleArea = self.MiddleArea.rstrip(',')
        self.SmallArea = self.SmallArea.rstrip(',')        
        print(f"Area code set to: {self.LargeArea}, {self.MiddleArea}, {self.SmallArea}")
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
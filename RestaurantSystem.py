import sys
from PySide6 import QtCore, QtScxml
import google.generativeai as genai
import logging
from telegram_bot import TelegramBot
from llm_concept_extractor import get_restaurant_info_from_utterance
from recruit import HotPepper, getAPI


class RestaurantSystem():
    
    # 状態とシステム発話を紐づけた辞書
    uttdic = {"None": "こちらは飲食店発掘システムです。\n \
・都道府県名\n \
・予算\n \
・ジャンル\n\
などに合わせておすすめの飲食店をお伝えします。",
              "ask_budget_or_genre": "希望するお店の予算やジャンルはありますか？",
              "ask_place_or_budget": "希望するお店の場所や予算はありますか？",
              "ask_place_or_genre": "希望するお店の場所やジャンルはありますか？",
              "ask_place": "希望するお店の場所はありますか？",
              "ask_budget": "希望するお店の予算はありますか？",
              "ask_genre": "希望するお店のジャンルはありますか？",
              "tell_info": "お伝えします。"
              }
    
    def __init__(self):
        # Qtに関するおまじない
        app = QtCore.QCoreApplication()
        
        # 対話セッションを管理するための辞書
        self.sessiondic = {}
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        google_api_key = getAPI("GoogleAPIKey")
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        if model is None:
            logging.error("Failed to initialize the Generative Model.")
            sys.exit(1)
        self.recruit = HotPepper()


    def initial_message(self, input):
        text = input["utt"]
        sessionId = input["sessionId"]

        self.el  = QtCore.QEventLoop()        

        # SCXMLファイルの読み込み
        sm  = QtScxml.QScxmlStateMachine.fromFile('recruit.scxml')

        # セッションIDとセッションに関連する情報を格納した辞書
        self.sessiondic[sessionId] = {"statemachine":sm, "place":"", "budget":"", "genre":""}

        # 初期状態に遷移
        sm.start()
        self.el.processEvents()
        self.recruit.setArea("")
        self.recruit.setBudget(0)
        self.recruit.setGenre("")

        # 初期状態の取得
        current_state = sm.activeStateNames()[0]
        print("current_state=", current_state)

        # 初期状態に紐づいたシステム発話の取得と出力
        sysutt = self.uttdic[current_state]

        return {"utt":sysutt, "end":False}
    
    
    def reply(self, input):
        text = input["utt"]
        sessionId = input["sessionId"]

        sm = self.sessiondic[sessionId]["statemachine"]
        current_state = sm.activeStateNames()[0]
        print("current_state=", current_state)
        
        info = get_restaurant_info_from_utterance(text)
        place = info["place"]
        budget = (info["budget"])
        genre = info["genre"]
        utts = []
        
        # イベントを処理
        if place[0] != "":
            value = self.recruit.setArea(place)
            if value == 0:
                print("申し訳ありませんが、指定された場所は認識できませんでした。")
                utts.append("申し訳ありませんが、指定された場所は認識できませんでした。")
                place = [""]
        if budget != "":
            self.recruit.setBudget(int(budget))
        if genre[0] != "":
            value = self.recruit.setGenre(genre)
            if value == 0:
                print("申し訳ありませんが、指定されたジャンルは認識できませんでした。")
                utts.append("申し訳ありませんが、指定されたジャンルは認識できませんでした。")
                genre = [""]
            

        # ユーザ入力を用いて状態遷移
        if current_state == "None":
            print("place=", place, "budget=", budget, "genre=", genre)
            if place[0] != "" and budget != "" and genre[0] != "":
                sm.submitEvent("place_and_budget_and_genre")
            elif place[0] != "" and budget != "":
                sm.submitEvent("place_and_budget")
            elif place[0] != "" and genre[0] != "":
                sm.submitEvent("place_and_genre")
            elif budget != "" and genre[0] != "":
                sm.submitEvent("budget_and_genre")
            elif place[0] != "":
                sm.submitEvent("place")
            elif budget != "":
                sm.submitEvent("budget")
            elif genre[0] != "":
                sm.submitEvent("genre")
        elif current_state == "ask_place_or_budget":
            if place[0] != "" and budget != "":
                sm.submitEvent("place_and_budget")
            elif place[0] != "":
                sm.submitEvent("place")
            elif budget != "":
                sm.submitEvent("budget")
        elif current_state == "ask_place_or_genre":
            if place[0] != "" and genre[0] != "":
                sm.submitEvent("place_and_genre")
            elif place[0] != "":
                sm.submitEvent("place")
            elif genre[0] != "":
                sm.submitEvent("genre")
        elif current_state == "ask_budget_or_genre":
            if budget != "" and genre[0] != "":
                sm.submitEvent("budget_and_genre")
            elif budget != "":
                sm.submitEvent("budget")
            elif genre[0] != "":
                sm.submitEvent("genre")
        elif current_state == "ask_place":
            if place[0] != "":
                sm.submitEvent("place")
        elif current_state == "ask_budget":
            if budget != "":
                sm.submitEvent("budget")
        elif current_state == "ask_genre":
            if genre[0] != "":
                sm.submitEvent("genre")
        else:
            print("Unknown state:", current_state)
            return {"utt": "申し訳ありませんが、現在の状態ではその情報を処理できません。", "end": True}
        
        # イベントを処理
        self.el.processEvents()
        if place[0] != "":
            self.sessiondic[sessionId]["place"] = place
            self.recruit.setArea(place)
        if budget != "":
            self.sessiondic[sessionId]["budget"] = budget
            self.recruit.setBudget(int(budget))
        if genre[0] != "":
            self.sessiondic[sessionId]["genre"] = genre
            self.recruit.setGenre(genre)

        # 遷移先の状態を取得
        current_state = sm.activeStateNames()[0]
        print("current_state=", current_state)

        # 遷移先がtell_infoの場合は情報を伝えて終了
        if current_state == "tell_info":
            utts.append("お伝えします。")
            NumberOfShops = self.recruit.getRestaurantInfo()
            if NumberOfShops == 0:
                utts.append("おすすめのお店は見つかりませんでした。")
                return {"utt": "申し訳ありませんが、条件に合う飲食店が見つかりませんでした。", "end": True}
            elif NumberOfShops < 0:
                utts.append("エラーが発生しました。")
                return {"utt": "システムエラーが発生しました。後ほど再度お試しください。", "end": True}
            else:
                utts.append(f"{NumberOfShops}件のおすすめの飲食店があります。")
            utts.append("\n".join(self.recruit.RestaurantNameList))
            utts.append("です。ご利用ありがとうございました。")
            del self.sessiondic[sessionId]
            return {"utt":"\n".join(utts), "end": True}

        else:
            # その他の遷移先の場合は状態に紐づいたシステム発話を生成
            utts.append(self.uttdic[current_state])
            return {"utt":"\n".join(utts), "end": False}
    
if __name__ == '__main__':
    system = RestaurantSystem()
    bot = TelegramBot(system)
    bot.run()
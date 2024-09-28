import logging
from tls_client import Session
from colorama import Fore
import random, string
import urllib.parse
import threading
import json
import os
import html
from bs4 import BeautifulSoup

config = json.load(open("input/config.json"))
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

streamHandler = logging.StreamHandler()
consoleFormatter = logging.Formatter(
    fmt=f"{Fore.CYAN}%(asctime)s{Fore.WHITE} . {Fore.RED}%(levelname)s{Fore.WHITE} . {Fore.LIGHTBLACK_EX}%(name)s{Fore.WHITE} ~ %(message)s",
    datefmt="%H:%M:%S"
)
streamHandler.setFormatter(consoleFormatter)
logger.addHandler(streamHandler)

with open('input/proxies.txt') as f:
    proxies = f.read().splitlines()

lock = threading.Lock()

class Chess(object):
    def __init__(self) -> None:
        self.client = Session(
            client_identifier="brave_129",
            pseudo_header_order=[":authority", ":method", ":path", ":scheme"],
            random_tls_extension_order=True
        )
        self.sec_ch_ua = "Brave\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        self.client.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "referer": "https://www.chess.com/",
            "sec-ch-ua": self.sec_ch_ua,
            "user-agent": self.user_agent
        }

    def get_email(self) -> str:
        return "".join(random.choices(string.ascii_lowercase+string.digits, k=12)) + random.choice(["@gmail.com", "@outlook.com"])
    
    def get_username(self) -> str:
        return "".join(random.choices(string.ascii_lowercase+string.digits+string.ascii_uppercase, k=25))

    def validate_email(self, email: str, _token: str) -> bool:
        return self.client.post("https://www.chess.com/callback/email/available", params={"email": email}, json={"token": _token}).status_code == 200

    def validate_username(self, username: str, _token: str) -> bool:
        return self.client.post("https://www.chess.com/callback/user/valid", params={"username": username}, json={"token": _token}).status_code == 200

    def get_session_id(self) -> str:
        return self.client.get("https://ssl.kaptcha.com/collect/sdk?m=850100").text.split("ka.sessionId='")[1].split("'")[0]

    def get_fingerprint(self) -> str:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=32))

    def get_token(self) -> str:
        resp = self.client.get("https://www.chess.com/register", timeout_seconds=60, allow_redirects=True, )
        json_data = BeautifulSoup(resp.text, "html.parser").find('div', attrs={'id': 'registration'})['data-form-params']
        token = json.loads(html.unescape(json_data))['token']['value']
        return token

    def get_payload(self) -> dict[str|int]:
        return {
            "registration[skillLevel]": "1",
            "registration[_token]": self.get_token(),
            "kountSessionId": self.get_session_id(),
            "fingerprint": self.get_fingerprint(),
            "registration[friend]": "",
            "registration[username]": self.get_username(),
            "registration[email]": self.get_email(),
            "registration[password]": "".join(random.choices(string.digits + string.ascii_uppercase, k=12)),
            "registration[timezone]": "Asia/Calcutta"
        }
    
    def register(self):
        try:
            proxy = random.choice(proxies)
            self.client.proxies = "http://" + proxy
            payload = self.get_payload()

            self.client.headers.update({"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"})
            self.client.headers.update({"content-type": "application/x-www-form-urlencoded"})
            resp = self.client.post("https://www.chess.com/register", data=urllib.parse.urlencode(payload), allow_redirects=True)

            if "uuid" in resp.text:
                uuid = resp.text.split('"uuid":"')[1].split('"')[0]
                logger.debug(f"Registered Account -> {uuid[:-4]}****")
                self.client.headers.update({"content-type": "application/json"})
                code = self.client.post("https://www.chess.com/rpc/chesscom.partnership_offer_codes.v1.PartnershipOfferCodesService/RetrieveOfferCode", json={
                    "campaignId": "4daf403e-66eb-11ef-96ab-ad0a069940ce",
                    "userUuid": uuid
                })
                logger.info(f"Code -> {code.json().get('codeValue')}")

                with lock:
                    with open('output/promos.txt', 'a') as f:
                        f.write(f"https://discord.com/billing/promotions/{code.json().get('codeValue')}\n")

        except Exception as e:
            return False, e

if __name__ == "__main__":
    os.system("cls" or "clear")
    thread_count = int(input(f"{Fore.BLUE}>>{Fore.WHITE} Threads -> "))

    while True:
        if threading.active_count() - 1 < int(thread_count):
            threading.Thread(target=Chess().register).start()

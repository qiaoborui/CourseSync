import requests
import hashlib
import re
from bs4 import BeautifulSoup
from datetime import datetime
from backend.academic_system_client import BaseAcademicSystemClient
from .encrypt import encrypt_password

class NWAFUAcademicSystemClient(BaseAcademicSystemClient):
    BASE_URL = "https://authserver.nwafu.edu.cn"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False
        self.is_authenticated = self.authenticate()

    def authenticate(self):
        salt, execution = self.get_salt_and_execution()
        enc_passwd = encrypt_password(self.password, salt)
        payload = {
            "username": self.username,
            "password": enc_passwd,
            "_eventId": "submit",
            "cllt": "userNameLogin",
            "execution": execution,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        resp = self.session.post(f'{self.BASE_URL}/authserver/login', data=payload, headers=headers,allow_redirects=False)
        return resp.status_code == 302

    def get_salt_and_execution(self):
        url = f'{self.BASE_URL}/authserver/login?service=https%3A%2F%2Fnewehall.nwafu.edu.cn%2Flogin%3Fservice%3Dhttps%3A%2F%2Fnewehall.nwafu.edu.cn%2Fywtb-portal%2FLite%2Findex.html%3Fbrowser%3Dno%23%2FcusHall'
        resp = self.session.get(url)
        #  <input type="hidden" id="pwdEncryptSalt" value="66R9pzYqIdbUfGfG"/>
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.find("input", {"id": "pwdEncryptSalt"})["value"], soup.find("input", {"id": "execution"})["value"]


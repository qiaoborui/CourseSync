import requests
import hashlib
import re
from bs4 import BeautifulSoup
from datetime import datetime
from backend.academic_system_client import BaseAcademicSystemClient
from .encrypt import encrypt_password
from http.cookies import SimpleCookie

class NWAFUAcademicSystemClient(BaseAcademicSystemClient):
    BASE_URL = "https://authserver.nwafu.edu.cn"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False
        self.is_authenticated = self.authenticate()
        self.current_semester = self.fetch_current_semester() if self.is_authenticated else None
        self.exams = []
        self.courses = []

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
        resp = self.session.post(f'{self.BASE_URL}/authserver/login', data=payload, headers=headers,allow_redirects=True)
        self.copy_cookies_to_new_domain("authserver.nwafu.edu.cn", "newehall.nwafu.edu.cn")
        task_url = f'https://newehall.nwafu.edu.cn/taskcenterapp/sys/taskCenter/taskNew/getMyProcessCount.do'
        resp = self.session.post(task_url)
        for cookie in self.session.cookies:
            print(f'{cookie.domain} {cookie.name} {cookie.value}')
        return resp.status_code == 200

    def copy_cookies_to_new_domain(self, old_domain, new_domain):
        new_cookies = SimpleCookie()
        for cookie in self.session.cookies:
            if old_domain in cookie.domain:
                new_cookie = SimpleCookie()
                new_cookie[cookie.name] = cookie.value
                new_cookie[cookie.name]['domain'] = new_domain
                new_cookie[cookie.name]['path'] = '/'
                new_cookies.update(new_cookie)
        
        for key, morsel in new_cookies.items():
            self.session.cookies.set(key, morsel.value, domain=new_domain, path='/')

    def get_salt_and_execution(self):
        url = f'{self.BASE_URL}/authserver/login?service=https%3A%2F%2Fnewehall.nwafu.edu.cn%2Flogin%3Fservice%3Dhttps%3A%2F%2Fnewehall.nwafu.edu.cn%2Fywtb-portal%2FLite%2Findex.html%3Fbrowser%3Dno%23%2FcusHall'
        resp = self.session.get(url)
        #  <input type="hidden" id="pwdEncryptSalt" value="66R9pzYqIdbUfGfG"/>
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.find("input", {"id": "pwdEncryptSalt"})["value"], soup.find("input", {"id": "execution"})["value"]

    def fetch_current_semester(self):
        weu_url = "https://newehall.nwafu.edu.cn/jwapp/sys/funauthapp/api/getAppConfig/wdkbby-5959167891382285.do"
        resp = self.session.get(weu_url)
        url = "https://newehall.nwafu.edu.cn/jwapp/sys/wdkbby/modules/jshkcb/dqxnxq.do"
        resp = self.session.post(url)
        return resp.json()["datas"]["dqxnxq"]["rows"][0]["DM"]
    
    def fetch_exams(self):
        pass

    def process_exam_data(self):
        pass

    def fetch_courses(self):
        url = "https://newehall.nwafu.edu.cn/jwapp/sys/wdkbby/modules/xskcb/xsdkkc.do"
        payload = {
            "XNXQDM": self.current_semester,
            "SKZC": 5,
            "*order": "-SQSJ",
            "querySetting": "[{\"name\":\"BYBZ\",\"builder\":\"notEqual\",\"linkOpt\":\"AND\",\"value\":\"1\"}]",
        }
        resp = self.session.post(url, data=payload)
        self.courses = resp.json()["datas"]["list"]

    def process_course_data(self):
        result = []
        for course in self.courses:
            course_info = {
                "lessonId": course["XNXQDM"] + course["KCH"],
                "courseName": course["KCM"],
                "personName": course["XSKJSXM"],
                "roomZh": course["XXXXQDM_DISPLAY"],
                "date": course["ZCMC"],
                "startTime": course["SQSJ"],
                "endTime": course["JSSJ"],
            }
            result.append(course_info)
        return result

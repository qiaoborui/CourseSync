import requests
import hashlib
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from ..base_client import BaseAcademicSystemClient
from .encrypt import encrypt_password
from http.cookies import SimpleCookie

class NWAFUAcademicSystemClient(BaseAcademicSystemClient):
    BASE_URL = "https://authserver.nwafu.edu.cn"
    EHALL_URL = "https://newehall.nwafu.edu.cn"
    JWAPP_URL = f"{EHALL_URL}/jwapp/sys"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False
        self.is_authenticated = self.authenticate()
        self.current_semester = self.fetch_current_semester() if self.is_authenticated else None
        self.first_week_date = self.fetch_first_week_date() if self.is_authenticated and self.current_semester else None
        self.exams = []
        self.courses = []
        self.class_time_map = self.create_class_time_map()

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
        resp = self.session.post(f'{self.BASE_URL}/authserver/login', data=payload, headers=headers, allow_redirects=True)
        self.copy_cookies_to_new_domain("authserver.nwafu.edu.cn", "newehall.nwafu.edu.cn")
        task_url = f'{self.EHALL_URL}/taskcenterapp/sys/taskCenter/taskNew/getMyProcessCount.do'
        resp = self.session.post(task_url)
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
        url = f'{self.BASE_URL}/authserver/login?service={self.EHALL_URL}%2Flogin%3Fservice%3D{self.EHALL_URL}%2Fywtb-portal%2FLite%2Findex.html%3Fbrowser%3Dno%23%2FcusHall'
        resp = self.session.get(url)
        #  <input type="hidden" id="pwdEncryptSalt" value="66R9pzYqIdbUfGfG"/>
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.find("input", {"id": "pwdEncryptSalt"})["value"], soup.find("input", {"id": "execution"})["value"]

    def fetch_current_semester(self):
        weu_url = f"{self.JWAPP_URL}/funauthapp/api/getAppConfig/wdkbby-5959167891382285.do"
        resp = self.session.get(weu_url)
        url = f"{self.JWAPP_URL}/wdkbby/modules/jshkcb/dqxnxq.do"
        resp = self.session.post(url)
        return resp.json()["datas"]["dqxnxq"]["rows"][0]["DM"]
    
    def fetch_exams(self):
        pass

    def process_exam_data(self):
        pass

    def fetch_first_week_date(self):
        weu_url = f"{self.JWAPP_URL}/funauthapp/api/getAppConfig/wdkbby-5959167891382285.do"
        resp = self.session.get(weu_url)
        url = f"{self.JWAPP_URL}/wdkbby/modules/xskcb/cxxljc.do"
        """
        XN: 2024-2025
        XQ: 1
        """
        payload = {
            "XN": self.current_semester[:9],
            "XQ": self.current_semester[-1:],
        }
        resp = self.session.post(url, data=payload)
        first_week_date = resp.json()["datas"]["cxxljc"]["rows"][0]["XQKSRQ"]
        # XQKSRQ: "2024-09-09 00:00:00"
        return datetime.strptime(first_week_date, "%Y-%m-%d %H:%M:%S").timestamp()

    def fetch_courses(self):
        url = f"{self.JWAPP_URL}/wdkbby/modules/xskcb/xsdkkc.do"
        payload = {
            "XNXQDM": self.current_semester,
            "*order": "-SQSJ",
            "querySetting": "[{\"name\":\"BYBZ\",\"builder\":\"notEqual\",\"linkOpt\":\"AND\",\"value\":\"1\"}]",
        }
        resp = self.session.post(url, data=payload)
        self.courses = resp.json()["datas"]["xsdkkc"]["rows"]

        zhkb_url = f"{self.JWAPP_URL}/wdkbby/modules/xskcb/cxxszhxqkb.do"
        resp = self.session.post(zhkb_url, data=payload)
        self.courses.extend(resp.json()["datas"]["cxxszhxqkb"]["rows"])

    def create_class_time_map(self):
        winter_map = {
            1: ("08:00", "08:40"),
            2: ("08:50", "09:30"),
            3: ("09:50", "10:30"),
            4: ("10:40", "11:20"),
            5: ("11:30", "12:10"),
            6: ("14:00", "14:40"),
            7: ("14:50", "15:30"),
            8: ("15:40", "16:20"),
            9: ("16:30", "17:10"),
            10: ("17:20", "18:00"),
            11: ("19:30", "20:10"),
            12: ("20:15", "20:55"),
            13: ("21:00", "21:40")
        }

        summer_map = {
            1: ("08:00", "08:40"),
            2: ("08:50", "09:30"),
            3: ("09:50", "10:30"),
            4: ("10:40", "11:20"),
            5: ("11:30", "12:10"),
            6: ("14:30", "15:10"),
            7: ("15:20", "16:00"),
            8: ("16:10", "16:50"),
            9: ("17:00", "17:40"),
            10: ("17:50", "18:30"),
            11: ("19:30", "20:10"),
            12: ("20:15", "20:55"),
            13: ("21:00", "21:40")
        }

        return {"winter": winter_map, "summer": summer_map}
    
    def calculate_date(self, week, day_of_week):
        """
        Calculate the date based on the week number and day of the week.
        
        :param week: int, the week number (1-based)
        :param day_of_week: int, the day of the week (1 for Monday, 7 for Sunday)
        :return: datetime object representing the calculated date
        """
        if not self.first_week_date:
            raise ValueError("First week date is not set")
        
        # Convert first_week_date from timestamp to datetime
        first_week_datetime = datetime.fromtimestamp(self.first_week_date)
        
        # Calculate the number of days to add
        days_to_add = (week - 1) * 7 + (day_of_week - 1)
        
        # Calculate the target date
        target_date = first_week_datetime + timedelta(days=days_to_add)
        
        return target_date

    def process_course_data(self):
        result = []
        for course in self.courses:
            # Determine if it's winter or summer based on the semester
            season = "winter" if int(self.current_semester[-1:]) == 1 else "summer"
            start_number = course["KSJC"]
            end_number = course["JSJC"]
            
            start_time = self.class_time_map[season][start_number][0]
            end_time = self.class_time_map[season][end_number][1]
            
            SKZC = course["SKZC"]
            week_numbers = [i for i in range(1, len(SKZC)+1) if SKZC[i-1] == "1"]
            for week_number in week_numbers:
                # Use get() method with a default value to avoid KeyError
                day_of_week = course.get("XSKXQ") or course.get("SKXQ")
                if day_of_week is None:
                    print(f"Warning: Missing day of week for course {course.get('KCM', 'Unknown')}")
                    continue
                
                date = self.calculate_date(week_number, int(day_of_week))
                course_info = {
                    "lessonId": course["XNXQDM"] + course["KCH"],
                    "courseName": course["KCM"],
                    "personName": course.get("XSKJSXM", course.get("SKJS")),
                    "roomZh": course.get("JASDM", "未知地点"),
                    "startTime": start_time,
                    "endTime": end_time,
                }
                # Convert date to string format and use it for parsing
                date_str = date.strftime("%Y-%m-%d")
                course_info["start"] = datetime.strptime(f"{date_str} {course_info['startTime']}", "%Y-%m-%d %H:%M")
                course_info["end"] = datetime.strptime(f"{date_str} {course_info['endTime']}", "%Y-%m-%d %H:%M")
                result.append(course_info)
        return result

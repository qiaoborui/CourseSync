import requests
import hashlib
import re
from bs4 import BeautifulSoup
from datetime import datetime
from academic_system_client import BaseAcademicSystemClient

class XAUATAcademicSystemClient(BaseAcademicSystemClient):
    BASE_URL = "https://swjw.xauat.edu.cn/student"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.is_authenticated = self.authenticate()
        self.current_semester = self.fetch_current_semester() if self.is_authenticated else None
        self.courses = []
        self.exams = []

    def authenticate(self):
        salt = self.session.get(f"{self.BASE_URL}/login-salt").text
        enc_passwd = hashlib.sha1(f"{salt}-{self.password}".encode('utf-8')).hexdigest()
        payload = {'username': self.username, 'password': enc_passwd, 'captcha': 'false'}
        resp = self.session.post(f"{self.BASE_URL}/login", json=payload)
        return resp.json().get('result', False)

    def fetch_current_semester(self):
        resp = self.session.get(f"{self.BASE_URL}/for-std/course-table").text
        match = re.search('selected" value="(.*?)"', resp)
        return match.group(1) if match else None

    def fetch_courses(self):
        if not self.is_authenticated or not self.current_semester:
            return False
        url = f'{self.BASE_URL}/for-std/course-table/get-data?bizTypeId=2&semesterId={self.current_semester}&dataId='
        try:
            resp = self.session.get(url).json()
            self.courses = resp['lessonIds']
            return True
        except Exception as e:
            print(f"Failed to fetch course list: {e}")
            return False

    def fetch_exams(self):
        url = f"{self.BASE_URL}/for-std/exam-arrange"
        try:
            resp = self.session.get(url).text
            soup = BeautifulSoup(resp, 'html.parser')
            table = soup.find('table', id='exams')
            self.exams = []
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                course = cols[0].text.strip()
                time = cols[1].text.strip()
                self.exams.append({'course': course, 'time': time})
            return True
        except Exception as e:
            print(f"Failed to fetch exam schedule: {e}")
            return False

    def process_exam_data(self):
        for exam in self.exams:
            date, time_range = exam['time'].split(' ')
            start, end = time_range.split('~')
            exam['start'] = datetime.strptime(f"{date} {start}", '%Y-%m-%d %H:%M')
            exam['end'] = datetime.strptime(f"{date} {end}", '%Y-%m-%d %H:%M')

    def fetch_course_details(self):
        if not self.courses:
            return None
        url = f"{self.BASE_URL}/ws/schedule-table/datum"
        resp = self.session.post(url, json={"studentId": "null", 'lessonIds': self.courses})
        return resp.json().get('result')

    def process_course_data(self):
        if not self.fetch_courses():
            return []
        data = self.fetch_course_details()
        if not data:
            return []
        
        course_dict = {lesson['id']: lesson['courseName'] for lesson in data['lessonList']}
        result = []
        for schedule in data['scheduleList']:
            schedule_info = {
                'lessonId': schedule['lessonId'],
                'courseName': course_dict.get(schedule['lessonId'], "Unknown Course"),
                'personName': schedule.get('personName', "Unknown Teacher"),
                'roomZh': "未知地点",
                'date': schedule['date'],
                'startTime': schedule['startTime'],
                'endTime': schedule['endTime']
            }
            
            if isinstance(schedule.get('room'), dict):
                schedule_info['roomZh'] = schedule['room'].get('nameZh', "未知地点")
            elif isinstance(schedule.get('room'), str):
                schedule_info['roomZh'] = schedule['room']

            date = schedule['date'].split('-')
            start = divmod(schedule['startTime'], 100)
            end = divmod(schedule['endTime'], 100)
            schedule_info['start'] = datetime(int(date[0]), int(date[1]), int(date[2]), start[0], start[1])
            schedule_info['end'] = datetime(int(date[0]), int(date[1]), int(date[2]), end[0], end[1])
            result.append(schedule_info)
        return result

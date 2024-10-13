import requests
import json
from datetime import datetime, timedelta
import hashlib
import re
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, Alarm, vDatetime
from flask import Flask, request, Response
import os
from abc import ABC, abstractmethod
import inspect
import sys

class BaseAcademicSystemClient(ABC):
    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def fetch_current_semester(self):
        pass

    @abstractmethod
    def fetch_courses(self):
        pass

    @abstractmethod
    def fetch_exams(self):
        pass

    @abstractmethod
    def process_exam_data(self):
        pass

    @abstractmethod
    def fetch_course_details(self):
        pass

    @abstractmethod
    def process_course_data(self):
        pass

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

class CalendarGenerator:
    @staticmethod
    def create_calendar(courses, exams):
        cal = Calendar()
        cal.add('X-WR-CALNAME', '课程表')
        cal.add('X-APPLE-CALENDAR-COLOR', '#540EB9')
        cal.add('X-WR-TIMEZONE', 'Asia/Shanghai')

        for exam in exams:
            event = Event()
            event.add('UID', f"exam-{exam['course']}-{exam['start'].isoformat()}")
            event.add('DTSTART', vDatetime(exam['start']))
            event.add('DTEND', vDatetime(exam['end']))
            event.add('SUMMARY', f"{exam['course']}考试")
            event.add('DESCRIPTION', f"考试时间: {exam['time']}")
            event.add('LOCATION', '考试地点: 请查看教务系统')
            
            alarm = Alarm()
            alarm.add('ACTION', 'DISPLAY')
            alarm.add('DESCRIPTION', f"{exam['course']}考试即将开始！")
            alarm.add('TRIGGER', timedelta(minutes=-30))
            event.add_component(alarm)
            
            cal.add_component(event)

        for course in courses:
            event = Event()
            event.add('UID', f"course-{course['lessonId']}-{course['start'].isoformat()}")
            event.add('DTSTART', vDatetime(course['start']))
            event.add('DTEND', vDatetime(course['end']))
            event.add('SUMMARY', course['courseName'])
            event.add('DESCRIPTION', course['personName'])
            event.add('LOCATION', course['roomZh'])
            
            alarm = Alarm()
            alarm.add('ACTION', 'DISPLAY')
            alarm.add('DESCRIPTION', f"{course['courseName']}课程在{course['roomZh']}即将开始！")
            alarm.add('TRIGGER', timedelta(minutes=-15))
            event.add_component(alarm)
            
            cal.add_component(event)

        return cal.to_ical()

# Factory for creating academic system clients
class AcademicSystemClientFactory:
    @staticmethod
    def create_client(school, username, password):
        # Get all classes in the current module
        classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        
        # Filter classes that inherit from BaseAcademicSystemClient
        academic_system_clients = [
            cls for name, cls in classes 
            if issubclass(cls, BaseAcademicSystemClient) and cls != BaseAcademicSystemClient
        ]
        
        # Find the client class for the specified school
        for client_class in academic_system_clients:
            if client_class.__name__.lower().startswith(school.lower()):
                return client_class(username, password)
        
        raise ValueError(f"Unsupported school: {school}")

class AcademicCalendarService:
    def __init__(self, school, username, password):
        self.client = AcademicSystemClientFactory.create_client(school, username, password)

    def generate_calendar(self):
        if not self.client.is_authenticated:
            return None

        self.client.fetch_courses()
        self.client.fetch_exams()
        courses = self.client.process_course_data()
        self.client.process_exam_data()

        return CalendarGenerator.create_calendar(courses, self.client.exams)

app = Flask(__name__)

@app.route('/class', methods=['GET'])
def get_academic_calendar():
    school = request.args.get('school', default='xauat')
    username = request.args.get('username')
    password = request.args.get('password') or request.args.get('passwd')
    if not username or not password:
        return "缺少用户名或密码", 400
    
    try:
        service = AcademicCalendarService(school, username, password)
        calendar_data = service.generate_calendar()
        
        if calendar_data is None:
            return "认证失败", 401
        
        return Response(calendar_data, mimetype='text/calendar')
    except ValueError as e:
        return str(e), 400

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000), host='0.0.0.0')
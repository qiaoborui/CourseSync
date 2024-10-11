import requests
import json
from datetime import datetime, timedelta
import hashlib
import re
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, Alarm, vDatetime
from flask import Flask, request, Response

class AcademicSystemClient:
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
                'roomZh': "Mystery Corner",
                'date': schedule['date'],
                'startTime': schedule['startTime'],
                'endTime': schedule['endTime']
            }
            
            if isinstance(schedule.get('room'), dict):
                schedule_info['roomZh'] = schedule['room'].get('nameZh', "Mystery Corner")
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
        cal.add('X-WR-CALNAME', 'Academic Calendar')
        cal.add('X-APPLE-CALENDAR-COLOR', '#540EB9')
        cal.add('X-WR-TIMEZONE', 'Asia/Shanghai')

        for exam in exams:
            event = Event()
            event.add('UID', f"exam-{exam['course']}-{exam['start'].isoformat()}")
            event.add('DTSTART', vDatetime(exam['start']))
            event.add('DTEND', vDatetime(exam['end']))
            event.add('SUMMARY', f"{exam['course']} Exam")
            event.add('DESCRIPTION', f"Exam time: {exam['time']}")
            event.add('LOCATION', 'Exam location: Please check the academic system')
            
            alarm = Alarm()
            alarm.add('ACTION', 'DISPLAY')
            alarm.add('DESCRIPTION', f"Exam {exam['course']} is about to start!")
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
            alarm.add('DESCRIPTION', f"{course['courseName']} in {course['roomZh']} is about to start!")
            alarm.add('TRIGGER', timedelta(minutes=-15))
            event.add_component(alarm)
            
            cal.add_component(event)

        return cal.to_ical()

class AcademicCalendarService:
    def __init__(self, username, password):
        self.client = AcademicSystemClient(username, password)

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
    username = request.args.get('username')
    password = request.args.get('passwd')
    if not username or not password:
        return "Missing username or password", 400
    
    service = AcademicCalendarService(username, password)
    calendar_data = service.generate_calendar()
    
    if calendar_data is None:
        return "Authentication failed", 401
    
    return Response(calendar_data, mimetype='text/calendar')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
import requests
import json
from datetime import datetime, timedelta
import hashlib
import re
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, Alarm
from flask import Flask, request, Response

class JwcClass:
    BASE_URL = "https://swjw.xauat.edu.cn/student"

    def __init__(self, username, passwd):
        self.username = username
        self.passwd = passwd
        self.session = requests.Session()
        self.status = self.login()
        self.semester = self.get_semester() if self.status else None
        self.class_list = []
        self.exam_list = []

    def get_semester(self):
        resp = self.session.get(f"{self.BASE_URL}/for-std/course-table").text
        match = re.search('selected" value="(.*?)"', resp)
        return match.group(1) if match else None

    def login(self):
        salt = self.session.get(f"{self.BASE_URL}/login-salt").text
        enc_passwd = hashlib.sha1(f"{salt}-{self.passwd}".encode('utf-8')).hexdigest()
        payload = {'username': self.username, 'password': enc_passwd, 'captcha': 'false'}
        resp = self.session.post(f"{self.BASE_URL}/login", json=payload)
        return resp.json().get('result', False)

    def get_class(self):
        if not self.status or not self.semester:
            return False
        url = f'{self.BASE_URL}/for-std/course-table/get-data?bizTypeId=2&semesterId={self.semester}&dataId='
        try:
            resp = self.session.get(url).json()
            self.class_list = resp['lessonIds']
            return True
        except Exception as e:
            print(f"获取课程清单失败: {e}")
            return False

    def get_exam(self):
        url = f"{self.BASE_URL}/for-std/exam-arrange"
        try:
            resp = self.session.get(url).text
            soup = BeautifulSoup(resp, 'html.parser')
            table = soup.find('table', id='exams')
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                course = cols[0].text.strip()
                time = cols[1].text.strip()
                self.exam_list.append({'course': course, 'time': time})
            return True
        except Exception as e:
            print(f"获取考试安排失败: {e}")
            return False

    def process_exam(self):
        self.get_exam()
        for exam in self.exam_list:
            date, time_range = exam['time'].split(' ')
            start, end = time_range.split('~')
            exam['start'] = datetime.strptime(f"{date} {start}", '%Y-%m-%d %H:%M')
            exam['end'] = datetime.strptime(f"{date} {end}", '%Y-%m-%d %H:%M')

    def get_detail(self):
        if not self.class_list:
            return None
        url = f"{self.BASE_URL}/ws/schedule-table/datum"
        resp = self.session.post(url, json={"studentId": "null", 'lessonIds': self.class_list})
        return resp.json().get('result')

    def edit_data(self):
        if not self.get_class():
            return []
        data = self.get_detail()
        if not data:
            return []
        
        course_dict = {lesson['id']: lesson['courseName'] for lesson in data['lessonList']}
        result = []
        for schedule in data['scheduleList']:
            schedule_info = {
                'lessonId': schedule['lessonId'],
                'courseName': course_dict.get(schedule['lessonId'], "未知课程"),
                'personName': schedule.get('personName', "未知教师"),
                'roomZh': "神秘的角落",
                'date': schedule['date'],
                'startTime': schedule['startTime'],
                'endTime': schedule['endTime']
            }
            
            # 安全地获取教室信息
            if isinstance(schedule.get('room'), dict):
                schedule_info['roomZh'] = schedule['room'].get('nameZh', "神秘的角落")
            elif isinstance(schedule.get('room'), str):
                schedule_info['roomZh'] = schedule['room']

            date = schedule['date'].split('-')
            start = divmod(schedule['startTime'], 100)
            end = divmod(schedule['endTime'], 100)
            schedule_info['start'] = datetime(int(date[0]), int(date[1]), int(date[2]), start[0], start[1])
            schedule_info['end'] = datetime(int(date[0]), int(date[1]), int(date[2]), end[0], end[1])
            result.append(schedule_info)
        return result

    def create_sheet(self):
        cal = Calendar()
        cal.add('X-WR-CALNAME', '课表')
        cal.add('X-APPLE-CALENDAR-COLOR', '#540EB9')
        cal.add('X-WR-TIMEZONE', 'Asia/Shanghai')

        events = self.edit_data()
        self.process_exam()

        for exam in self.exam_list:
            event = Event()
            event.add('UID', exam['time'])
            event.add('DTSTART', exam['start'])
            event.add('DTEND', exam['end'])
            event.add('SUMMARY', f"{exam['course']} 考试")
            event.add('DESCRIPTION', f"考试时间：{exam['time']}")
            event.add('LOCATION', '考试地点：请查看教务系统')
            alarm = Alarm()
            alarm.add('ACTION', 'DISPLAY')
            alarm.add('TRIGGER', timedelta(minutes=-10))
            alarm.add('DESCRIPTION', f"考试{exam['course']}快要开始了！")
            event.add_component(alarm)
            cal.add_component(event)

        for schedule in events:
            event = Event()
            event.add('UID', schedule['end'].isoformat())
            event.add('DTSTART', schedule['start'])
            event.add('DTEND', schedule['end'])
            event.add('SUMMARY', schedule['courseName'])
            event.add('DESCRIPTION', schedule['personName'])
            event.add('LOCATION', schedule['roomZh'])
            alarm = Alarm()
            alarm.add('ACTION', 'DISPLAY')
            alarm.add('TRIGGER', timedelta(minutes=-10))
            alarm.add('DESCRIPTION', f"在{schedule['roomZh']}上课的{schedule['courseName']}快要开始了！")
            event.add_component(alarm)
            cal.add_component(event)

        return cal.to_ical()

app = Flask(__name__)

@app.route('/class', methods=['GET'])
def get_class_schedule():
    username = request.args.get('username')
    passwd = request.args.get('passwd')
    if not username or not passwd:
        return "Missing username or password", 400
    
    stu = JwcClass(username, passwd)
    if not stu.status:
        return "Login failed", 401
    
    return Response(stu.create_sheet(), mimetype='text/calendar')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True,port=5001)
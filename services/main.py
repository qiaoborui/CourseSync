import requests
import json
from datetime import datetime
import hashlib
from icalendar import Calendar, Event, Alarm
from datetime import datetime, timedelta
from flask import Flask,request,Response
import re
from bs4 import BeautifulSoup

class JwcClass:
    def __init__(self,username,passwd) -> None:
        self.username = username
        self.passwd = passwd
        self.session = requests.session()
        self.status = self.login()
        self.semester = self.getSemester()
        self.classList=[]
        self.examList = []

    def getSemester(self):
        resp = self.session.get("https://swjw.xauat.edu.cn/student/for-std/course-table").text
        match = re.search('selected" value="(.*?)"',  resp)
        if match:
            return match.group(1)


    def login(self):
        resp = self.session.get("https://swjw.xauat.edu.cn/student/login-salt")
        salt = resp.text
        encpasswd = hashlib.sha1((salt+'-'+self.passwd).encode('utf-8')).hexdigest()
        payload={'username': self.username,'password': encpasswd,'captcha':'false'}
        rsp = self.session.post("https://swjw.xauat.edu.cn/student/login",data=json.dumps(payload),headers={'Content-Type':'application/json'})
        data = json.loads(rsp.text)
        if data['result']:
            return True
        else:
            return False

    def getClass(self):
        if not self.status:
            return
        url = f'https://swjw.xauat.edu.cn/student/for-std/course-table/get-data?bizTypeId=2&semesterId={self.semester}&dataId='
        try:
            resp = self.session.get(url).json()
            self.classList = resp['lessonIds']
            print('课程清单如下：')
            print(resp['lessonIds'])
        except:
            print("获取课程清单失败...")
            return
    
    def getExam(self):
        url = "https://swjw.xauat.edu.cn/student/for-std/exam-arrange"
        try:
            resp = self.session.get(url).text
            soup = BeautifulSoup(resp,'html.parser')
            # <table class="table table-bordered table-striped table-hover table-condensed" id="exams"> 根据 id 获取表格
            table = soup.find('table',id='exams')
            # 跳过表头
            for row in table.find_all('tr')[1:]:
                # 获取每一行的所有列
                cols = row.find_all('td')
                """
                <td>编译原理 
                  
                </td>
                                    <td class="time">2024-05-22 10:30~12:30</td>
                                    <td>草堂8-106</td>
                                    <!--<td th:if="${isDisplaySeatNo}" th:text="${model.examGroup.examPlacePublished and model.seatNo != null} ? ${model.seatNo}"></td>-->
                                    <td id="seat-1700565"></td>
                                    <td>8号楼</td>
                                    <td>草堂校区</td>
                """
                # 拿到课程名称，考试时间
                course = cols[0].text.strip()
                time = cols[1].text.strip()
                self.examList.append({'course':course,'time':time})
            return
        except:
            print("获取考试安排失败...")

    def processExam(self):
        # DTSTART:20240529T102500
        # DTEND:20240529T122500
        self.getExam()
        for i in self.examList:
            time = i['time'].split(' ')
            date = time[0]
            start = time[1].split('~')[0]
            end = time[1].split('~')[1]
            start = start.split(':')
            end = end.split(':')
            i['start'] = datetime.strptime(date+start[0]+start[1],'%Y-%m-%d%H%M')
            i['end'] = datetime.strptime(date+end[0]+end[1],'%Y-%m-%d%H%M')

    def getDetail(self):
        if len(self.classList)==0:
            return 
        url = "https://swjw.xauat.edu.cn/student/ws/schedule-table/datum"
        resp = self.session.post(url,data=json.dumps({"studentId":"null",'lessonIds':self.classList}),headers={"Content-Type":"application/json"}).json()
        data = resp['result']
        return data

    def editData(self):
        self.getClass()
        data = self.getDetail()
        dict = {}#名称和id对应
        result = []
        for i in data['lessonList']:
            dict[i['id']]=i['courseName']
        for i in data['scheduleList']:
            del i['scheduleGroupId']
            del i['periods']
            del i['weekIndex']
            del i['experiment']
            del i['teacherId']
            del i['personId']
            del i['customPlace']
            i["courseName"] = dict[i['lessonId']]
            try:
                i["roomZh"] = i['room']['nameZh']
            except:
                i["roomZh"] = "神秘的角落"
            del i['room']
            time = i['date'].split('-')
            start = [str(i['startTime'])[0:-2],str(i['startTime'])[-2:]]
            end = [str(i['endTime'])[0:-2],str(i['endTime'])[-2:]]
            i['start'] = datetime(int(time[0]),int(time[1]),int(time[2]),int(start[0]),int(start[1]))
            i['end'] = datetime(int(time[0]),int(time[1]),int(time[2]),int(end[0]),int(end[1]))
        result = data['scheduleList']
        return result

    def createSheet(self):
        cal = Calendar()
        cal.add('X-WR-CALNAME','课表')
        cal.add('X-APPLE-CALENDAR-COLOR','#540EB9')
        cal.add('X-WR-TIMEZONE','Asia/Shanghai')
        events = self.editData()
        self.processExam()
        for i in self.examList:
            event=Event()
            event.add('UID',i['time'])
            event.add('DTSTART',i['start'])
            event.add('DTEND',i['end'])
            event.add('SUMMARY',f"{i['course']} 考试",)
            event.add('DESCRIPTION',f"考试时间：{i['time']}")
            event.add('LOCATION','考试地点：请查看教务系统')
            alarm=Alarm()
            alarm.add('ACTION', 'DISPLAY')
            alarm.add('TRIGGER', timedelta(minutes=-10))
            desc = f"考试{i['course']}快要开始了！"
            alarm.add('DESCRIPTION', desc)
            event.add_component(alarm)
            cal.add_component(event)
        for i in events:
            event=Event()
            event.add('UID',i['end'])
            event.add('DTSTART',i['start'])
            event.add('DTEND',i['end'])
            event.add('SUMMARY',i['courseName'])
            event.add('DESCRIPTION',f"{i['personName']}")
            event.add('LOCATION',i['roomZh'])
            alarm=Alarm()
            alarm.add('ACTION', 'DISPLAY')
            alarm.add('TRIGGER', timedelta(minutes=-10))
            desc = f"在{i['roomZh']}上课的{i['courseName']}快要开始了！"
            alarm.add('DESCRIPTION', desc)
            event.add_component(alarm)
            cal.add_component(event)
        return cal.to_ical()

app = Flask(__name__)
@app.route('/class',methods = ['GET'])
def hello_world():
    username = request.args.get('username')
    passwd = request.args.get('passwd')
    stu = JwcClass(username,passwd)
    return Response(stu.createSheet(), mimetype='text/calendar')

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
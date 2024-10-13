from icalendar import Calendar, Event, Alarm, vDatetime
from datetime import timedelta

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

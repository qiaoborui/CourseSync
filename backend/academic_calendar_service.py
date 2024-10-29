from school.xauat.xauat_client import XAUATAcademicSystemClient
from school.nwafu.nwafu_client import NWAFUAcademicSystemClient
from calendar_generator import CalendarGenerator

class AcademicSystemClientFactory:
    @staticmethod
    def create_client(school, username, password):
        # Map school names to their respective client classes
        clients = {
            'xauat': XAUATAcademicSystemClient,
            'nwafu': NWAFUAcademicSystemClient,
            # Add other schools and their clients here
        }
        
        school_key = school.lower()
        if school_key in clients:
            return clients[school_key](username, password)
            
        raise ValueError(f"Unsupported school: {school}")

class AcademicCalendarService:
    def __init__(self, school, username, password):
        self.client = AcademicSystemClientFactory.create_client(school, username, password)

    def generate_calendar(self, event_filter=None):
        if not self.client.is_authenticated:
            return None

        self.client.fetch_courses()
        self.client.fetch_exams()
        courses = self.client.process_course_data()
        self.client.process_exam_data()

        return CalendarGenerator.create_calendar(courses, self.client.exams, event_filter)

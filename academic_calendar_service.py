import inspect
import sys
from xauat_client import XAUATAcademicSystemClient
from calendar_generator import CalendarGenerator
from academic_system_client import BaseAcademicSystemClient

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

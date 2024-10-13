import os
import importlib
import inspect
from school.base_client import BaseAcademicSystemClient
from calendar_generator import CalendarGenerator

class AcademicSystemClientFactory:
    @staticmethod
    def create_client(school, username, password):
        client_directory = 'school'
        
        academic_system_clients = []
        for root, dirs, files in os.walk(client_directory):
            for file in files:
                if file.endswith('_client.py'):
                    module_path = os.path.join(root, file).replace('/', '.').replace('\\', '.')[:-3]
                    module = importlib.import_module(module_path)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, BaseAcademicSystemClient) and obj != BaseAcademicSystemClient:
                            academic_system_clients.append(obj)
                            
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

from abc import ABC, abstractmethod

class BaseAcademicSystemClient(ABC):
    @abstractmethod
    def authenticate(self):
        pass

    def fetch_current_semester(self):
        pass

    def fetch_courses(self):
        pass

    def fetch_exams(self):
        pass

    def process_exam_data(self):
        pass

    def fetch_course_details(self):
        pass

    def process_course_data(self):
        pass

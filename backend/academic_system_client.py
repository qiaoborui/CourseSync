from abc import ABC, abstractmethod

class BaseAcademicSystemClient(ABC):
    @abstractmethod
    def authenticate(self):
        pass

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
    def process_course_data(self):
        pass

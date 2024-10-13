from abc import ABC, abstractmethod
from typing import List, Dict, TypedDict
from datetime import datetime

class CourseInfo(TypedDict):
    lessonId: str
    courseName: str
    personName: str
    roomZh: str
    start: datetime
    end: datetime

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
    def process_course_data(self) -> List[CourseInfo]:
        """
        Process and standardize course data.

        Returns:
            List[CourseInfo]: A list of CourseInfo dictionaries, where each dictionary
            represents a course with the following structure:
            {
                'lessonId': str,
                'courseName': str,
                'personName': str,
                'roomZh': str,
                'start': datetime,
                'end': datetime
            }
        """
        pass

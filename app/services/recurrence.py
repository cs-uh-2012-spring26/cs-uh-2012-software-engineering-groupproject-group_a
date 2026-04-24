from abc import ABC, abstractmethod
from datetime import timedelta


class RecurrenceStrategy(ABC): #define interface as Abstract Base Class
    @abstractmethod #any subclass that doesn’t implement it cannot be instantiated
    def generate_occurrences(self, first_start, first_end, recurrence_end):
        raise NotImplementedError


class DailyRecurrenceStrategy(RecurrenceStrategy):
    def generate_occurrences(self, first_start, first_end, recurrence_end):
        occurrences = []
        current_start = first_start
        class_duration = first_end - first_start

        #Keep generating one occurrence every day until recurrence_end
        while current_start <= recurrence_end:
            occurrences.append({
                "start_time": current_start,
                "end_time": current_start + class_duration,
            })
            current_start += timedelta(days=1)

        return occurrences


class WeeklyRecurrenceStrategy(RecurrenceStrategy):
    def generate_occurrences(self, first_start, first_end, recurrence_end):
        occurrences = []
        current_start = first_start
        class_duration = first_end - first_start

        #Keep generating one occurrence every week until recurrence_end
        while current_start <= recurrence_end:
            occurrences.append({
                "start_time": current_start,
                "end_time": current_start + class_duration,
            })
            current_start += timedelta(weeks=1)

        return occurrences
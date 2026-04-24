# Redesign Report

## Feature 6 : Create recurrence classes

**Design Pattern**: 

*Strategy* - Defines a set of algorithms, puts each into a separate class, and makes their objects interchangeable. The user is able to replace one object by another during runtime.

**Why**: 

Feature 6 is best suited to the Strategy pattern because recurring-class creation requires selecting one of several scheduling algorithms at runtime, such as daily or weekly generation.

The system was refactored so that the API doesn't contain recurrence-specific branching logic. The service layer delegates occurrence generation to a RecurrenceStrategy implementation, while existing validation and persistence stay in the current service and ClassResource classes.

This improves adherence to the Open–Closed Principle because adding a new recurrence type, such as biweekly, only requires adding another strategy class rather than modifying the existing class-creation flow.

**Refactoring**:

- Introduced a RecurrenceStrategy hierarchy under app/services/recurrence.py.
- Refactored scheduling logic out of the API layer into services/classes.py (create_recurring_classes_with_validation), reusing existing validation functions.
- Modified ClassList.post in apis/classes.py to be closed for changes: single-class creation remains unchanged, recurring logic is handled by strategies and a thin service layer.

**Why it fixes previous smells**:

- Avoids bloating post() with multiple recurrence branches (solves Long Method).
- Makes recurrence extension a matter of adding a new strategy (satisfies Open–Closed).
- Keeps scheduling logic centralized and reusable across single and recurring flows.
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

## Design Violation & Code Smell Fixes

### Encapsulation of remaining_spots (3.1.1):
Fixed the encapsulation violation around class capacity by removing direct access to the remaining_spots field from apis/bookings.py. Instead of reading the raw database field name in the API layer, the booking flow now calls ClassResource.has_remaining_spots(class_id).

### Role strings and primitive obsession, encapsulation of authorization logic (3.1.2, 4.2.1):
Fixed the primitive obsession and role-encapsulation issue by replacing scattered string literals such as "member" and "trainer" with a dedicated Role enum in db/users.py. The API layer now calls create_user(..., role=Role.MEMBER) and create_user(..., role=Role.TRAINER), so valid roles are centralized and type-like rather than being treated as arbitrary text. Also added helper methods such as is_admin, is_trainer, and user_has_management_access to move permission-related behavior into UserResource, which improves encapsulation and removes duplicated authorization logic.

### Open-Closed Principle for registration (3.4.1):
Fixed the Open-Closed Principle violation in registration by separating registration into RegisterMember and RegisterTrainer endpoints. Previously, registration logic was tied to one flow that always created a member, so supporting trainer registration required modifying existing behavior. In the refactored design, new registration behavior is added through separate endpoint classes while UserResource.create_user() accepts a role parameter, making the registration flow easier to extend without rewriting the original member-registration logic.

### Long Method BookClass.post (4.1.1):
Reviewed the long-method concern in BookClass.post(), but after refactoring the capacity access and keeping the method in a flat early-return style, the controller remained readable enough for its current responsibilities, so no additional decomposition was introduced beyond the encapsulation fix.

### Dead code in users.py, auth.py (4.5.1):
Removed dead code in db/users.py by deleting the unused serialize_items import. 

Removed the dead-code issue in apis/auth.py by replacing the unused old role import pattern with the actively used Role enum.





>> ## Team member responsibilities:
>>  - Isumi: Refactors for Design Principle Violations 3.1.1, 3.1.2, 3.4.1 & Code Smells 4.1.1, 4.2.1, 4.5.1, Feature 6 Create recurring classes implementation, Class diagram creation
>>  - Nada: 
>>  - Rujul: 

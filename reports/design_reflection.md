# Design Reflection

## 1. Executive Summary

### 1.1 Approach

- **Goal:** Critically analyze the current system design to prepare for Feature 6 (recurring classes) and Feature 7 (configurable notifications).

- **Tools used:**
  - UML support (sequence-diagram generator) to create initial Book Class endpoint sequence diagram.
  - Manual inspection of modules and tests to validate and refine diagrams and findings.

- **Manual analysis:**
  - Traced end-to-end flows for:
    - Authentication and authorization.
    - API layer
    - DB layer
  - Reviewed code for:
    - Violations of OOD and SOLID principles.
    - Code smells

- **Team member responsibilities:**
  - Isumi: Sequence diagram fo Book Class endpoint, identify design principle violations and code smells for Book Class flow and authentication flow
  - Nada: Class diagram to show main classes and their associations, identify design principle violations and code smells for Create Class flow and View Class List
  - Rujul: Sequence diagram for the notification endpoint, identified design principle violations and code smells in the code related to sending reminders and viewing the class members list

---

## 2. Design Diagrams (Task 1)

### 2.1. Class Diagram – Current Design
![Class Diagram](class_diagram.png)

### 2.2. Sequence Diagram – Book a Class Endpoint

### 2.3. Sequence Diagram – Reminder/Notification Endpoint
![Sequence Diagram – Reminder/Notification Endpoint](sequence_diagram_notification_endpoint.png)

---

## 3. Design Principles Reflection (Task 2)

### 3.1. Encapsulation (OOD Principle)

#### 3.1.1. Example 1
- **Location:** `app/db/classes.py` and `app/apis/bookings.py` – `method name` - imported from `classes.py` at `line 3` in `bookings.py`, used in `line 75`

<img src="design_reflection_screenshots/apis-bookings-line3.png" alt="Screenshot for Section 3.1.1 showing the import and use of remaining_spots in bookings.py" width="500"><br>

<img src="design_reflection_screenshots/apis-bookings-line75.png" alt="Screenshot for Section 3.1.1 showing the import and use of remaining_spots in bookings.py" width="500"><br>

- **Description:**
  - The API layer directly imports and uses the DB field name `remaining_spots` to check whether a class is full.
- **Why it’s a violation:**
  - This breaks encapsulation because the API layer knows the internal field name used by the DB layer. The logic for deciding whether a class is full should be hidden behind a method in `ClassResource`, instead of exposing raw schema details. In the current design, if the DB field name changes, the API code also has to change.
- **Possible refactor:** 
  - Add a method such as `is_class_full(class_id)` in `ClassResource` and let the API call that instead of checking remaining_spots directly.

#### 3.1.2. Example 2
- **Location:** `app/db/users.py` - `create_user()` - `line 13`, `line 27`

<img src="design_reflection_screenshots/db-users-line13-27.png" alt="Screenshot for Section 3.1.2 showing the role represented as strings" width="500"><br>  

- **Description:**
  - User roles are represented as raw strings, and authorization logic is based on string comparisons scattered across the codebase.
- **Why it’s a violation:**
  - This breaks encapsulation because there is no central authorization helper or module that defines what roles exist and what permissions each role has. The meaning of roles is spread across the system instead of being controlled in one place. So adding a new role or changing permissions would require searching through multiple files and updating string-based checks manually.
- **Possible refactor:** 
  - Introduce a centralized authorization helper, role enum, or permission-checking method so role definitions and access rules are managed in one place.

#### 3.1.3. Example 3
- **Location:** `app/db/classes.py` and `app/apis/classes.py` - DB field-name constants imported from classes.py at line 4 in apis/classes.py, defined in db/classes.py at lines 9–17, used in apis/classes.py at lines 103–108 

<img src="design_reflection_screenshots/db-classes-lines-9-17.png" alt="Screenshot for Section 3.1.3 definition of above mentioned variables in db/classes.py" width="500"><br>

<img src="design_reflection_screenshots/apis-classes-lines-4.png" alt="Screenshot for Section 3.1.3 import of above mentioned variables in apis/classes.py" width="500"><br>

<img src="design_reflection_screenshots/apis-classes-lines-103-108.png" alt="Screenshot for Section 3.1.3 use of above mentioned variables in apis/classes.py" width="500"><br>  

- **Description:**
  - The API layer directly imports and uses DB field names such as class_name, start_time, end_time, location, capacity, trainer_name and remaining_spots.
- **Why it’s a violation:**
  - This breaks encapsulation because the API layer knows the internal details of the DB layer. Instead of using methods from ClassResource, the API directly uses field names. In the current design, if any field name changes in db/classes.py, the API code must also change.
- **Possible refactor:** 
  - Hide these details behind methods in ClassResource, such as get_class_data(...) so the API does not depend directly on DB constants.

### 3.1.4. Example 4
- **Location:** `app/apis/classes.py` - `ClassList.post()` - `lines 139–150`

<img src="design_reflection_screenshots/apis-classes-lines-139-150.png" alt="Screenshot for Section 3.1.4 showing the get_upcoming_classes_grouped_by_week()" width="500"><br>  

- **Description:**
  - The API layer directly inspects the structure returned by ClassResource().get_upcoming_classes_grouped_by_week() by looping through grouped classes, reading raw dictionary fields and reparsing stored date strings.
- **Why it’s a violation:**
  - This breaks encapsulation because the API layer knows too much about how class data is stored and returned. It knows that the result is grouped by week, that each class is represented as a dictionary and that date fields are stored as ISO strings. If the return structure changes, the API logic must change too.
- **Possible refactor:** 
  - Move this logic into ClassResource so the API doesn’t have to deal with internal data details.
### 3.2. Modularity (OOD Principle)
#### 3.2.1. Example 1 - High Coupling 
- **Location:** `app/apis/classes.py` - `ClassList.post()`- `lines 97–101, 139, 153–154` 

<img src="design_reflection_screenshots/apis-classes-lines-97-101.png" alt="Screenshot for Section 3.2.1 showing the high coupling example in classes.py" width="500"><br>

<img src="design_reflection_screenshots/apis-classes-lines-139.png" alt="Screenshot for Section 3.2.1 showing the high coupling example in classes.py" width="500"><br>

<img src="design_reflection_screenshots/apis-classes-lines-153-154.png" alt="Screenshot for Section 3.2.1 showing the high coupling example in classes.py" width="500"><br>

- **Description:**
  - The API endpoint directly constructs and depends on concrete classes such as UserResource() and ClassResource().
- **Why it’s a violation:**
  - This is an example of high coupling because the API depends on the internal structure and behavior of multiple components instead of interacting through simple interfaces.
- **Possible refactor:** 
  - Introduce a service layer so the API is less tightly coupled to concrete DB or resource implementations.




### 3.3. Single Responsibility Principle

#### 3.3.1. Example 1

- **Location:** `app/apis/classes.py` - `ClassMembers.get()` - `lines 195-219`

<img src="design_reflection_screenshots/apis-classes-lines195-219.png" alt="Screenshot for Section 3.3.1 ClassMembers.get() showing auth block, class lookup, booking fetch, and member assembly all in one method" width="500"><br>  

- **Description:**
  - The `ClassMembers.get()` method performs multiple distinct responsibilities in a single method: it authorizes the user, checks that the class exists, fetches all bookings for the class, and then fetches and formats each member's details.

- **Why it’s a violation:**
  - SRP states that a method should have only one reason to change. This method would need to be modified if the authorization logic changes, if the booking retrieval logic changes, or if the member data formatting changes. These are three independent reasons to modify the same method, making it harder to maintain and test in isolation.

- **Possible refactor:** 
  - Extract the different responsibilities as helper methods so the API method only handles HTTP concerns.

#### 3.3.2. Example 2

- **Location:** `app/apis/classes.py` - `ClassList.post()` - `lines 92–155`

<img src="design_reflection_screenshots/apis-classes-lines-92-102.png" alt="Screenshot for Section 3.3.2 ClassList.post() showing authorization, input validation, datetime parsing, scheduling constraints, overlap checking and class creation all in one method" width="500"><br>  

<img src="design_reflection_screenshots/apis-classes-lines-103-122.png" alt="Screenshot for Section 3.3.2 ClassList.post() showing authorization, input validation, datetime parsing, scheduling constraints, overlap checking and class creation all in one method" width="500"><br>  

<img src="design_reflection_screenshots/apis-classes-123-136.png" alt="Screenshot for Section 3.3.2 ClassList.post() showing authorization, input validation, datetime parsing, scheduling constraints, overlap checking and class creation all in one method" width="500"><br>  

<img src="design_reflection_screenshots/apis-classes-138-151.png" alt="Screenshot for Section 3.3.2 ClassList.post() showing authorization, input validation, datetime parsing, scheduling constraints, overlap checking and class creation all in one method" width="500"><br>  

- **Description:**
  - This method handles request validation, authorization, input validation, datetime parsing, scheduling constraints, overlap checking, class creation and response formatting.

- **Why it’s a violation:**
  - This violates SRP because the method has multiple reasons to change. A change in request format, validation rules, scheduling rules or overlap rules would all require modifying this same method.

- **Possible refactor:** 
  - Extract smaller methods.

### 3.4. Open-Close Principle

#### 3.4.1. Example 1

- **Location:** `app/db/users.py` - `create_user()` - `line 21`\
& `app/apis/auth.py` - `Register.post()` calling `create_user()` - `line 66`

<img src="design_reflection_screenshots/db-users-line13-27.png" alt="Screenshot for Section 3.4.1 showing the member role set as default" width="500"><br>  

<img src="design_reflection_screenshots/apis-auth-line66.png" alt="Screenshot for Section 3.4.1 showing the create_user call with member string" width="500"><br>

- **Description:**
  - User creation is implemented so that new users are always created as `"member"` from the registration flow, and the registration logic is not structured to support other role-specific registration paths.
- **Why it’s a violation:**
  - This violates the Open–Closed Principle because adding a new registration path (for example, a trainer-specific registration that assigns `"trainer"`) would require modifying the existing `Register.post()` logic or `create_user` behavior instead of simply adding a new extension (a different registration endpoint or strategy). The current design is not “closed to modification” when new roles or registration flows are needed.
- **Possible refactor:** 
  - Introduce role-aware registration strategies or separate registration endpoints (e.g., `MemberRegister`, `TrainerRegister`) that point to a common user-creation service, allowing new flows to be added without changing the existing ones.

#### 3.4.2. Example 2

- **Location:** `app/apis/classes.py` - `SendReminders.post()` calls `send_reminder_email` - `line 312`

<img src="design_reflection_screenshots/apis-classes-line312.png" alt="Screenshot for Section 3.4.2 showing the send_reminder_email call" width="500"><br>  

- **Description:**
  - The reminder sending logic is hardcoded to call `send_reminder_email()` directly. There is no abstraction layer between the API method and the specific email implementation.

- **Why it’s a violation:**
  - OCP states that a class/method should be open for extension but closed for modification. To add any new channel, `SendReminders.post()` would need to be directly modified rather than extended. The method is not closed for modification when requirements change.

- **Possible refactor:** 
  - Introduce an abstract `NotificationSender` base class and create concrete subclasses like `EmailNotificationSender`, `TelegramNotificationSender` etc. `SendReminders.post()` would then depend on the abstraction and new channels can be added without touching existing code

#### 3.4.3. Example 3

- **Location:** `app/apis/classes.py` - `ClassList.post()` - `line 100`\

<img src="design_reflection_screenshots/apis-classes-lines-100.png" alt="Screenshot for Section 3.4.3 showing the trainer and admin being hard-coded" width="500"><br>  

- **Description:**
  - Authorization is hardcoded using the string literals "trainer" and "admin".
- **Why it’s a violation:**
  - This violates the Open-Closed Principle because if a new role is added or the permission rules change, the existing logic has to be changed directly instead of being extended.
- **Possible refactor:** 
  - Instead of checking roles directly, use a helper like can_create_class(user) or a separate module to handle permissions.


### 3.5. Dependency Inversion Principle

#### 3.5.1. Example 1

- **Location:** `app/apis/classes.py` - import of `send_reminder_email` from `app.services.email` and its usage in `SendReminders.post()` - `line 312` \

<img src="design_reflection_screenshots/apis-classes-line312.png" alt="Screenshot for Section 3.5.1 showing the used of send_reminder_email method" width="500"><br>  

- **Description:**
  - `SendReminders` is a high-level API resource class that directly imports and calls the low-level concrete function `send_reminder_email` from `app.services.email`

- **Why it’s a violation:**
  - DIP states that high-level modules should not depend on low-level modules and both should depend on abstractions. Here the high-level `SendReminders` class is tightly coupled to the specific email implementation. If the notification mechanism changes, the high-level class must change too.

- **Possible refactor:** 
  - Introduce a `NotificationService` abstract interface into `SendReminders` so the high-level class depends on the abstraction rather than the concrete email function

---

## 4. Code Smells (Task 3)

### 4.1. Long Method

#### 4.1.1. `BookClass.post`
- **Location:** `app/apis/bookings.py` – `BookClass.post` - `line 56 - 87`

<img src="design_reflection_screenshots/apis-bookings-line56-87.png" alt="Screenshot for Section 4.1.1 showing the long BookClass.post method" width="500"><br> 

- **Why:**
  - The method spans more than 10 lines and handles multiple responsibilities: reading the request, validating the class, checking for duplicate bookings, enforcing capacity and race conditions, creating the booking, and formatting the response. This makes it harder to understand and maintain; any change to the booking rules requires working inside a long, multi-purpose method.
- **Refactoring suggestion:** 
  - Use Extract Method to split out responsibilities into smaller helpers like `get_and_validate_class(...)`, `ensure_not_already_booked(...)`, `reserve_spot(...)`, `create_booking_record(...)`. 
  This would make `post()` have a clear high-level flow.

### 4.2. Primitive Obsession

#### 4.2.1. Roles as plain strings
- **Location:** `app/db/users.py` – `ROLE = "role"` and usage - `line 13, line 27`\
& `app/apis/auth.py` - `Register.post()` calls `create_user()` with `role="member"` - `line 66`

<img src="design_reflection_screenshots/db-users-line13-27.png" alt="Screenshot for Section 4.2.1 showing the roles represented as strings" width="500"><br> 

<img src="design_reflection_screenshots/apis-auth-line66.png" alt="Screenshot for Section 4.2.1 showing the create_user call with default member string" width="500"><br> 

- **Why:**
  - The domain concept `“user role” ("member", "trainer", "admin")` is represented everywhere as plain strings.
`ROLE = "role"` identifies the field, but the actual role values are arbitrary strings with no central definition of what roles exist and what permissions they imply.
This matches the Primitive Obsession smell because a domain concept with its own rules (who can create classes, who can send reminders, who can manage schedules) is encoded as primitives instead of a dedicated type.
Because roles are just strings, typos or inconsistent naming wouldn’t be caught at compile time, and to add a new role or change permissions, we will have to search for and update multiple string comparisons throughout the code.


- **Refactoring suggestion:** 
  - Introduce a `Role` enum or similar abstraction (`Role.MEMBER`, `Role.TRAINER`, `Role.ADMIN`), and store these values in the DB.
And can use permission checks to define allowed roles, etc.


### 4.3. Long Parameter List

#### 4.3.1. Example 1
- **Location:** `app/apis/classes.py` – `SendReminders.post()` calling `send_reminder_email` `line 312`, and `app/services/email.py` – `send_reminder_email()` definition

<img src="design_reflection_screenshots/apis-classes-line312.png" alt="Screenshot of the send_reminder_email call in SendReminders.post() showing all five arguments" width="500"><br> 

- The call to `send_reminder_email` passes five individual arguments extracted from separate variables.

- **Refactoring suggestion:** 
  - Introduce a parameter object to group these arguments into a ReminderData dataclass so callers pass one object instead of five primitives, reducing coupling between the caller and the function signature.

### 4.4. Duplicate Code

#### 4.4.1. Example 1
- **Location:** `app/apis/classes.py` – `ClassMembers.get()` and `SendReminders.post()` - `lines 267-278` and `lines 196-208`

<img src="design_reflection_screenshots/apis-classes-lines267-278.png" alt="Screenshot showing the identical auth block and class-existence check in both methods" width="500"><br> 

- Both `ClassMembers.get()` and `SendReminders.post()` methods contain identical blocks of code for authorization and checking the existence of a class.

- **Refactoring suggestion:** 
  - Extract shared helper methods such as `authorize_trainer()` and `get_class(class_id)` and have both methods call them. This removes duplication and improves readability.

### 4.5. Dead Code

#### 4.5.1. Unused imports

- `serialize_items` in `users.py`
    - **Location:** `app/db/users.py` – `module import` - `line 1`

    <img src="design_reflection_screenshots/db-users-line1.png" alt="Screenshot for Section 4.5.1 showing the unused import serialize_items" width="500"><br> 

    - **Why:**
        - `serialize_items` is imported from `app/db/utils.py` but never used anywhere in `users.py`.
    According to the Dead Code smell, unused imports/variables add noise and can confuse future maintainers.
    - **Refactoring suggestion:** 
        - Remove the unused serialize_items import from `users.py`.

- `ROLE` in `auth.py`
    - **Location:** `app/apis/auth.py` – `module import` - `line 4`

    <img src="design_reflection_screenshots/apis-auth-line4.png" alt="Screenshot for Section 4.5.1 showing the unused import ROLE" width="500"><br> 

    - **Why:**
        - ROLE is imported from `app/db/users.py` but not actually used in `auth.py`.
        Instead, the registration endpoint uses `role="member"` as a string literal when calling `create_user`, so the imported constant is redundant.
    - **Refactoring suggestion:** 
        - Remove the unused `ROLE` import, or consistently use the `ROLE` constant instead of hardcoded strings.

---

## 5. Reflection on New Features (Task 4)

### 5.1. Overall Maintainability and Extensibility

#### for Feature 6 Recurring Classes: 
- Because booking logic and scheduling logic are tightly coupled in `BookClass.post`, if we want to add features like book whole series, skip one occurrence, update all future times - we will have to modify that method and related code in several places, rather than extending via new strategies or services. This links back to the earlier Open–Closed Principle, and would worsen Long Method smell (4.1.1).

#### for Feature 7 Configurable Notifications:

### 5.2. Existing Design Flaws

#### impacting Feature 6 Recurring Classes: 
- Because `BookClass.post` mixes responsibilities (load class, validate, check duplicate bookings, capacity, create record), if we add recurring-logic paths (book a particular occurrence vs entire series, enforce series-level limits) this would further bloat this method. This is a Long Method smell (4.1.1) and an Open–Closed Principle violation because to support recurring classes, we must modify the existing `post()`.

- For recurring classes, the role issues will still apply since there will be role-based permissions like how only trainers can create/modify a series. Because roles are currently plain strings (`"member", "trainer", "admin"`), to expand authorization rules for new recurring-class operations, we may have to add more string comparisons (`if user.role == "trainer":`, etc.) across booking and scheduling code, amplifying the Primitive Obsession smell (4.2.1).


#### impacting Feature 7 Configurable Notifications:  
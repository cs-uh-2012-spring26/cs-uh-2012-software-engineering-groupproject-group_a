# 1. Requirements Elicitation and Analysis

## Client Meeting Information
- **Date of Meeting:** February 11, 2026 
- **Duration:** 30 minutes

## Elicitation Techniques Used

1. **Structured Interviewing**
   - We prepared an extensive list of functional and non-functional questions.
   - We asked about expected system behavior, edge cases, constraints, and priorities.

2. **Scenario-Based Discussion**
   - We presented hypothetical user scenarios.
   - We asked how the system should respond in different situations.

3. **Use Case Discussion**
   - We discussed the four major system features.
   - We clarified actors and system boundaries.

## Reflection

### (1) Usefulness of Techniques

The structured form of interviewing with pre defined questions was very useful because it ensured we covered all major system aspects and avoided missing key requirements. It also helped uncover edge cases and clarify ambiguous behaviors.

In retrospect, we would improve our process by:
- Bringing wireframes to better visualize system interactions.

### (2) Important Clarification Gained

During the elicitation process, we clarified the distinction between registered members and unregistered guests. The client specified that only registered members should be allowed to book classes, while unregistered users may only view available classes.

This clarification directly impacted our backend design by requiring authentication mechanisms and role-based access to enforce these restrictions. Additionally, the client discussed potential future enhancements involving expanded administrative roles and functionality, which encouraged us to design the system with scalability in mind.

---

# 2. Requirements Specification

## UML Use Case Diagram

![Use Case Diagram](UML_Use_Case_Diagram.png)

### Use Case Specifications

### Feature 1: Create Class

### Feature 2: View Class List

### Feature 3: Book a Class

**Use Case:** Book a Class <br>

**Primary Actor:** Member (authenticated user) <br>

**Preconditions:** 
- User is registered and authenticated as a member (valid JWT).
- The class to be booked exists in the system. <br>

**Main Success Scenario:**
1. Member views the list of upcoming classes and chooses a specific class to book.
2. Member submits a booking request for that class.
3. System verifies that the class exists.
4. System verifies that the member has not already booked this class.
5. System verifies that the class is not full (there is at least one remaining spot).
6. System decrements the class’s remaining spots and creates a booking record linking the member to the class.
7. System returns a confirmation message and stores the booking so it appears in the member’s “My Classes” view.

**Extensions:**
- 3a. If the class does not exist, the system returns an error indicating “Class not found.”
- 4a. If the member has already booked this class, the system returns an error indicating the class is already booked by this user.
- 5a. If the class is full (no remaining spots), the system returns an error indicating the class is full and does not create a booking.
- 2a. If the booking request is missing or has an invalid class identifier, the system returns a validation error.

**Success guarantee:**
- A new booking exists linking the member to the selected class, and the class’s remaining spots have been reduced by one. The booking appears in the member’s “My Classes” list.


### Feature 4: View Bookings for a Class

**Use Case:**  View Bookings for a Class<br>
**Primary Actor:** Trainer <br>
**Preconditions:** User is authenticated as trainer<br>

**Main Success Scenario:**
1. Trainer selects a class to view bookings
2. System checks that the selected class exists
3. System retrieves all bookings for selected class
4. System displays the details of members who have booked the class

**Extensions:**
- 2a. If the class selected does not exist, system displays an error message
- 3a. In case of no bookings yet, system displays a placeholder message

**Success guarantee:**
- The system returns the booking list for the selected class

---








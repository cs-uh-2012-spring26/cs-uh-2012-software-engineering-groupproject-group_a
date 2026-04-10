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
  - Isumi: 
  - Nadja:
  - Rujul:

---

## 2. Design Diagrams (Task 1)

### 2.1. Class Diagram – Current Design

### 2.2. Sequence Diagram – Book a Class Endpoint

### 2.3. Sequence Diagram – Reminder/Notification Endpoint

---

## 3. Design Principles Reflection (Task 2)

### 3.1. Encapsulation (OOD Principle)

#### 3.1.1. Example
- **Location:** `file path` – `method name` - `line number`
- insert code screenshot
- **Description:**
  - ...
- **Why it’s a violation:**
  - ...
- **Possible refactor:** (optional)
  - Extract methods like `...`.

### 3.2. Modularity (OOD Principle)

### 3.3. Single Responsibility Principle

### 3.4. Open-Close Principle

### 3.5. Dependency Inversion Principle

---

## 4. Code Smells (Task 3)

### 4.1. Long Method

#### 4.1.1. `BookClass.post(...)`
- **Location:** `file path` – `method name` - `line number`
- insert code screenshot
- **Why:**
  - ...
- **Refactoring suggestion:** (optional)
  - Use **Extract Method** to ....

### 4.2. Primitive Obsession

### 4.3. Long Parameter List

### 4.4. Duplicate Code

### 4.5. Dead Code

---

## 5. Reflection on New Features (Task 4)

### 5.1. Overall Maintainability and Extensibility

#### for Feature 6 Recurring Classes: 
#### for Feature 7 Configurable Notifications:

### 5.2. Existing Design Flaws

#### impacting Feature 6 Recurring Classes: 
#### impacting Feature 7 Configurable Notifications:  
# Customer Support Ticket Data Dictionary

## 1. Overview
This dataset contains customer support ticket records captured across multiple communication channels (Email, Web Portal, Chat). It serves as the primary data source for the **Customer Support Ticket Analytics and GenAI Business Assistant** pipeline.

---

## 2. Column Specifications

| Column Name | Data Type (Source) | Target Data Type | Description | Allowed / Example Values | Nullable? | Used in Analytics? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ticket_id` | String | TEXT (PK) | Unique identifier for each ticket | `TKT-1001`, `TKT-1002` | **No** (Primary Key) | Yes (Counting, Deduplication) |
| `customer_id` | String | TEXT | Anonymised unique customer identifier | `CUST-5001`, `CUST-5022` | No | Yes (Repeat customer tracking) |
| `created_at` | String | DATETIME | Timestamp when ticket was logged by customer | `2026-03-01 09:15:00` (ISO format) | **No** | Yes (Volume trends, Resolution time) |
| `resolved_at` | String | DATETIME | Timestamp when ticket was resolved or closed | `2026-03-01 16:30:00` | **Yes** (NULL if Open/Pending) | Yes (Resolution duration calculation) |
| `category` | String | TEXT | Functional domain of the complaint | `Delivery & Shipping`, `Billing & Refunds`, `Product Quality`, `Technical Support`, `Customer Service` | No | Yes (Top categories, Unresolved hotspots) |
| `priority` | String | TEXT | Urgency level assigned to the ticket | `Critical`, `High`, `Medium`, `Low` | No | Yes (Priority breakdown & SLAs) |
| `status` | String | TEXT | Current operational workflow state | `Open`, `Pending`, `Resolved`, `Closed` | No | Yes (Open vs Closed metrics) |
| `subject` | String | TEXT | Short summary / title of the problem | `"Double charged for subscription"` | No | Yes (GenAI context & search) |
| `description` | String | TEXT | Full description provided by the customer | Detailed complaint narrative | No | Yes (GenAI qualitative analysis) |
| `resolution_notes`| String | TEXT | Notes logged by support agent upon resolution | Action taken, refund ID, courier tracking | **Yes** (NULL if unresolved) | Yes (Audit trail & resolution review) |

---

## 3. Business Rules & Integrity Constraints

1. **Uniqueness:** `ticket_id` must be globally unique across all records. Duplicate `ticket_id` records are rejected or deduplicated.
2. **Date Hierarchy:** If `resolved_at` is populated, `resolved_at >= created_at`. A resolution date earlier than the creation date indicates data corruption.
3. **Status & Resolution Timestamp Coupling:**
   - If `status` is `'Open'` or `'Pending'`, `resolved_at` must normally be `NULL`.
   - If `status` is `'Resolved'` or `'Closed'`, `resolved_at` should ideally have a valid timestamp.
4. **Calculated Field (Derived in Transformation Layer):**
   - `resolution_time_hours`: `(resolved_at - created_at)` in hours (float).
   - `is_unresolved`: `1` if `status IN ('Open', 'Pending')` else `0`.

---

## 4. Analytical Mapping (Master Prompt Section 4.D)

| Business Question | Required Fields | Calculation Method |
| :--- | :--- | :--- |
| **Q1: Total tickets received** | `ticket_id` | `COUNT(ticket_id)` |
| **Q2: Most common complaint categories** | `category`, `ticket_id` | `COUNT(*) GROUP BY category ORDER BY count DESC` |
| **Q3: Status distribution** | `status`, `ticket_id` | `COUNT(*) GROUP BY status` |
| **Q4: Average resolution time** | `resolution_time_hours` | `AVG(resolution_time_hours) WHERE status IN ('Resolved', 'Closed')` |
| **Q5: Categories with most unresolved tickets** | `category`, `is_unresolved` | `SUM(is_unresolved) GROUP BY category ORDER BY count DESC` |
| **Q6: Ticket volumes over time** | `created_at`, `ticket_id` | `COUNT(*) GROUP BY DATE(created_at)` |
| **Q7: Priorities needing management attention** | `priority`, `status`, `category`| Multi-dimensional filtering (`Critical` & `High` unresolved tickets) |

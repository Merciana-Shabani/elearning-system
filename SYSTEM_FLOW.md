# Elening LMS — System Flow

This document describes the main user journeys and how the main features connect.

---

## 1. Registration & roles

- **Signup** (`/accounts/signup/`): User chooses role **Student**, **Instructor**, or **Moderator** (and for Student: DPA or Normal Staff).
- **Instructor/Moderator at signup**: Must provide a unique **staff code**; they get that role immediately.
- **Student at signup**: Gets Student role. To become an Instructor, a **moderator** must change their role (see Moderator flow).

**Post-registration login**: Users are sent to their dashboard (students/instructors → My Dashboard; moderators → Moderation Dashboard).

---

## 2. Student flow

- **My Dashboard**: Enrolled courses, study list, progress.
- **Training**: Browse courses (`/courses/`), enroll (open or with key), view content, complete modules, get grades/certificates where applicable.
- **Profile**: View/edit own profile.

---

## 3. Instructor flow (approved or chosen at signup)

- **Dashboard**: Enrolled courses (if any) and **Courses I teach**.
- **Courses** (`/courses/teaching/`): Create courses, add modules/lessons, set enrollment type (open, manual, invite), submit for moderation.
- **Course lifecycle**: Draft → **Submit for approval** → Moderator **approves** / **rejects** / **returns for revision** (with reason/notes). Approved courses become visible; revision goes back to instructor.
- **Enrollment**: Open enrollment (and optional key), manual approval, or invite-only. View/manage enrollments per course.
- **Other**: Live briefings (conferences), quizzes, grades, announcements.

**Becoming an Instructor**: Either chosen at registration (with staff code) or a **moderator** changes the user’s role to Instructor on the User moderate page.

---

## 4. Moderator flow

- **Moderation Dashboard** (`/moderation/`): Platform overview (pending submissions, flagged content, disputes, users, courses, enrollments). Personal enrolled/taught courses and quick links.
- **Pending course reviews** (`/courses/pending/`): Approve, reject (with reason), or **return for revision** (with notes). Only submitted courses appear here.
- **Flagged content** (`/moderation/reports/`): Review reports, resolve (e.g. hide/remove content, add notes).
- **Disputes** (`/moderation/disputes/`): View and manage open/closed disputes.
- **Users** (`/users/`): List users; “View recent users” for newest first. Open a user to moderate them.
- **User moderate** (`/moderation/users/<id>/`): **Change role** (Student, Instructor, Moderator, Administrator) to make a user an Instructor or other role. Also: warn, suspend, or ban with reason; view audit log.
- **Enrollments** (`/moderation/enrollments/`): List all enrollments (user, course, date, status). “View enrollments” on dashboard goes here (not the course list).
- **Course categories** (`/courses/categories/manage/`): Create, rename, deactivate categories.

---

## 5. Course & enrollment flow

- **Instructor**: Creates course → adds content → submits for approval.
- **Moderator**: Approves / rejects / returns for revision. Approved courses are visible (according to visibility/date rules).
- **Student**: Browses courses → enrolls (open or with key) or requests (manual/invite). Access to content, assignments, grades as configured.
- **Enrollments**: Counts on Moderation Dashboard; full list under “View enrollments” for moderators.

---

## 6. Quick reference: who sees what

| Feature              | Student | Instructor | Moderator |
|----------------------|--------|------------|-----------|
| My Dashboard         | ✓      | ✓          | → Moderation Dashboard |
| Create / manage courses | —   | ✓          | ✓ (own)   |
| Pending course review | —     | —          | ✓         |
| Change user role (e.g. to Instructor) | — | — | ✓         |
| Enrollments list     | —      | per course | ✓ (all)   |
| User list / moderate | —      | —          | ✓         |
| Course categories    | —      | —          | ✓         |
| Flagged content / disputes | — | —     | ✓         |

---

## 7. Key URLs

- **Home**: `/`
- **Dashboard (redirect)**: `/dashboard/` → student/instructor dashboard or moderation dashboard
- **Moderation Dashboard**: `/moderation/`
- **Enrollments (moderator)**: `/moderation/enrollments/`
- **User moderate (change role)**: `/moderation/users/<id>/`
- **Users (moderator)**: `/users/`
- **Pending courses**: `/courses/pending/`
- **My courses (student)**: `/enrollment/my-courses/`
- **Teaching (instructor)**: `/courses/teaching/`

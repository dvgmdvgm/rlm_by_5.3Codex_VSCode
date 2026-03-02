# Spec: Review Notification Routing & Auto-Read

> Date: 2026-02-28
> Origin: /anchor_plan

## Objective

Fix two related issues with "leave a review" notifications after contract completion:
1. **Wrong navigation**: Clicking the notification in mobile app routes to job/applications page instead of the review screen.
2. **Auto-read**: After submitting a review, the related "leave a review" notification should be auto-marked as read (both web and mobile/API).

---

## Architecture & Context

- **Notification model**: `jobs/models.py` — `Notification` with `category`, `related_id`, `extra_data` (JSONField)
- **Notification creation for reviews**: `jobs/utils.py` (`check_user_contract_reviews()`) and `jobs/management/commands/check_contracts.py`
- **Web review view**: `jobs/views.py` `leave_review()` (+ duplicate in `jobs/jobs_views.py`)
- **API review creation**: `core/api_views.py` `ReviewViewSet.perform_create()`
- **Mobile notification routing**: `artconnect-mobile/app/src/screens/NotificationsScreen.jsx` (`getNotifRoute()`)
- **Mobile push banner routing**: `artconnect-mobile/app/src/components/NotificationBanner.jsx` (`resolveRoute()`)
- **Mobile review screen**: `artconnect-mobile/app/src/screens/LeaveReviewScreen.jsx` (route: `/review/:applicationId`)
- **Mobile contract API**: `contractsApi.get(applicationId)` returns `artist`, `employer`, `job` info
- **Utility**: `jobs/utils.py` `mark_related_notifications_read(user, category, related_id)`

### Root Cause Analysis

**Problem 1 — Wrong route**:
- Review notifications are created with `link=reverse('job_applications', ...)` (employer) or `link=reverse('my_applications')` (artist).
- Mobile routing functions resolve these links to `/jobs/{id}/applications` or `/applications` — NOT to `/review/{applicationId}`.
- The `extra_data` has `application_id` but nothing distinguishes a "leave review" notification from a generic contract notification.

**Problem 2 — No auto-read**:
- Neither `leave_review()` web view nor `ReviewViewSet.perform_create()` call `mark_related_notifications_read()` after saving the review.

---

## Proposed Changes

### Part A: Backend — Tag review notifications with action

- [ ] **A1. `jobs/utils.py` `check_user_contract_reviews()`** (lines 160-185):
  - Change `link` for employer review notif to: `reverse('leave_review', args=[app.id])` → `/application/{app_id}/review/`
  - Change `link` for artist review notif to: `reverse('leave_review', args=[app.id])` → `/application/{app_id}/review/`
  - Add `'action': 'leave_review'` to `extra_data` dict for both employer and artist notifications.

- [ ] **A2. `jobs/management/commands/check_contracts.py`** (lines 32-56):
  - Same changes as A1: fix `link` and add `'action': 'leave_review'` to `extra_data`.

### Part B: Backend — Auto-mark notifications read after review

- [ ] **B1. `core/api_views.py` `ReviewViewSet.perform_create()`** (line 931):
  - After `serializer.save(author=self.request.user)`, get the `application` from the saved review.
  - If `review.application` exists, call `mark_related_notifications_read(self.request.user, 'contract', review.application.id)`.

- [ ] **B2. `jobs/views.py` `leave_review()`** (line 578):
  - After `review.save()`, add: `mark_related_notifications_read(request.user, 'contract', application.id)`.

- [ ] **B3. `jobs/jobs_views.py` `leave_review()`** (duplicate view):
  - Same change as B2.

### Part C: Mobile — Fix notification routing to review screen

- [ ] **C1. `NotificationsScreen.jsx` `getNotifRoute()`**:
  - Add early check at the top of the function: if `extra.action === 'leave_review' && applicationId` → return `/review/${applicationId}`.
  - Also add link-based detection: if `link.includes('/review/')` → extract applicationId and return `/review/${applicationId}`.

- [ ] **C2. `NotificationBanner.jsx` `resolveRoute()`**:
  - Same logic as C1: detect `action === 'leave_review'` in `data` or `/review/` in link → return `/review/${applicationId}`.

### Part D: Mobile — LeaveReviewScreen must work without location.state

- [ ] **D1. `LeaveReviewScreen.jsx`**:
  - When `location.state` is empty/missing (e.g., navigated from notification), fetch application data via `contractsApi.get(applicationId)`.
  - From the response, determine `targetUserId` (if current user is employer → target is artist, and vice versa).
  - Show a loading spinner while fetching.

---

## Data Flow (after fix)

```
Contract ends
  → check_contracts.py / check_user_contract_reviews()
    → creates Notification:
        category='contract'
        related_id=application.id
        link='/application/{id}/review/'
        extra_data={job_id, application_id, action: 'leave_review'}
  
User clicks notification (mobile):
  → getNotifRoute() detects action='leave_review'
  → navigates to /review/{applicationId}
  → LeaveReviewScreen loads
    → if no location.state → fetch from contractsApi.get()
    → determines target user (artist or employer)
    → user submits review
      → reviewsApi.create() → POST /api/reviews/
      → ReviewViewSet.perform_create()
        → saves review
        → mark_related_notifications_read(user, 'contract', app.id)
        → notification auto-marked as read

User clicks notification (web):
  → mark_notification_read() → marks is_read=True → redirects to /application/{id}/review/
  → leave_review() view renders the review form
  → user submits
    → review.save()
    → mark_related_notifications_read(user, 'contract', app.id)
    → any remaining related notifs also marked read
```

---

## Verification & Tests

- [ ] Run `python manage.py check` — no errors
- [ ] Manually test: create a completed contract, trigger `check_contracts`, verify notification has `action: 'leave_review'` in `extra_data`
- [ ] Mobile: click review notification → should navigate to `/review/{applicationId}` and load target info
- [ ] Mobile: submit review → reload notifications → the notification should show as read
- [ ] Web: click review notification → should redirect to `leave_review` page
- [ ] Web: submit review → notification should be marked as read
- [ ] Edge case: click notification when review already submitted → `leave_review()` shows "already reviewed" warning + notification is still marked read

---

## Estimated Scope

- **Files changed**: 6 files (3 backend, 3 mobile)
- **Estimated size**: Medium (~60-80 lines changed)
- **Risk**: Low — additive changes, no schema migrations required

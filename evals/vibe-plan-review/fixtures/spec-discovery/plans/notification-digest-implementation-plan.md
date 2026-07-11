# Notification Digest Implementation Plan

## Goal

Send signed-in users one daily email digest of their unread in-app
notifications.

## Scope

- In scope: a daily digest job, digest email rendering, and a per-user opt-out
  toggle on the notification settings screen.
- Out of scope: real-time push notifications, SMS delivery, and notification
  center redesign.

## Acceptance Criteria

- Users with unread notifications receive one digest email per day.
- Users without unread notifications receive no digest email.
- The opt-out toggle stops future digest emails for that user.

## Implementation Tasks

- [ ] Inspect the notification read-state model and the existing mailer setup.
- [ ] Add the daily digest job that selects users with unread notifications.
- [ ] Render the digest email from unread notification titles and links.
- [ ] Add the opt-out toggle to the notification settings screen.
- [ ] Add tests for digest selection, empty-digest suppression, and opt-out.

## Verification

- Run `pnpm test -- notification-digest`.

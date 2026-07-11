# Notification Digest Requirements Spec

## Goal

Send signed-in users one daily email digest of their unread in-app
notifications.

## Requirements

- The digest email is sent at most once per user per calendar day in the user's
  account timezone.
- Only notifications unread at send time appear in the digest.
- Users with zero unread notifications receive no digest email that day.
- A per-user opt-out toggle on the notification settings screen stops future
  digest emails.
- Digest sending must not mark notifications as read.

## Acceptance Criteria

- A user with unread notifications receives exactly one digest email per day.
- A user with no unread notifications receives no digest email.
- Opted-out users receive no digest emails while opted out.
- Receiving a digest does not change any notification read state.

## Out Of Scope

- Real-time push notifications.
- SMS delivery.
- Notification center redesign.
- Marketing or announcement emails.

# Three-Day Agile Sprint

## Trello workflow

Board: [Hotel Booking Service](https://trello.com/b/1C5FZifF/hotel-booking-service)

Use four columns:

1. `To Do`
2. `In Progress`
3. `On Review`
4. `Done`

Each card represents one task and one pull request. A card moves to
`On Review` when the PR is open and moves to `Done` only after merge.

The table below is the planning source of truth. Trello is the daily execution
board: use it to change status, assign real team members, and attach pull
request links.

## Labels

Sprint labels:

- `Day 1`
- `Day 2`
- `Day 3`

Domain labels:

- `Rooms`
- `Users`
- `Bookings`
- `Payments`
- `Notifications`
- `Infrastructure`

Use the red `Blocked` label only when a dependency prevents work.

## Equal allocation

Each developer receives four cards and approximately 15 focused working hours.
Real names and Trello members can replace the placeholders during planning.
The project lead's initialization card is tracked separately and does not
change the equal feature allocation below.

| Developer | Cards | Time |
| --- | ---: | ---: |
| Developer 1 | 4 | 15 h |
| Developer 2 | 4 | 15 h |
| Developer 3 | 4 | 15 h |
| Developer 4 | 4 | 15 h |
| Developer 5 | 4 | 15 h |
| Developer 6 | 4 | 15 h |

## Cards

| ID | Task | Owner | Time | Day | Domain | Depends on |
| --- | --- | --- | ---: | --- | --- | --- |
| HBS-00 | Project applications, Docker, and CI scaffold | Serhii Sobka | 6 h | Day 1 | Infrastructure | None |
| HBS-01 | Create rooms app and Room model | Developer 1 | 3 h | Day 1 | Rooms | HBS-00 |
| HBS-02 | Implement Rooms CRUD endpoints | Developer 1 | 5 h | Day 1 | Rooms | HBS-01 |
| HBS-03 | Add room permissions and filters | Developer 1 | 3 h | Day 2 | Rooms | HBS-02 |
| HBS-04 | Implement room availability calendar | Developer 1 | 4 h | Day 2 | Rooms | HBS-02, HBS-11 |
| HBS-05 | Create users app and email-based user | Developer 2 | 4 h | Day 1 | Users | HBS-00 |
| HBS-06 | Add registration and profile endpoints | Developer 2 | 4 h | Day 1 | Users | HBS-05 |
| HBS-07 | Configure JWT obtain and refresh | Developer 2 | 3 h | Day 1 | Users | HBS-05 |
| HBS-08 | Add user permissions, tests, and docs | Developer 2 | 4 h | Day 2 | Users | HBS-06, HBS-07 |
| HBS-09 | Create Booking model and statuses | Developer 3 | 4 h | Day 1 | Bookings | HBS-01, HBS-05 |
| HBS-10 | Add booking list, detail, filters, permissions | Developer 3 | 4 h | Day 2 | Bookings | HBS-09 |
| HBS-11 | Implement booking creation and validation | Developer 3 | 5 h | Day 2 | Bookings | HBS-02, HBS-09 |
| HBS-12 | Add booking CRUD tests and API docs | Developer 3 | 2 h | Day 3 | Bookings | HBS-10, HBS-11 |
| HBS-13 | Implement booking cancellation flow | Developer 4 | 4 h | Day 2 | Bookings | HBS-11 |
| HBS-14 | Implement booking check-in flow | Developer 4 | 2 h | Day 2 | Bookings | HBS-11 |
| HBS-15 | Implement check-out and overstay flow | Developer 4 | 4 h | Day 2 | Bookings | HBS-11 |
| HBS-16 | Implement daily no-show task and tests | Developer 4 | 5 h | Day 3 | Bookings | HBS-11, HBS-22 |
| HBS-17 | Configure Telegram bot and message helper | Developer 5 | 3 h | Day 1 | Notifications | None |
| HBS-18 | Send booking and no-show notifications | Developer 5 | 3 h | Day 2 | Notifications | HBS-11, HBS-16, HBS-17 |
| HBS-19 | Send cancellation and payment notifications | Developer 5 | 3 h | Day 2 | Notifications | HBS-13, HBS-23 |
| HBS-20 | Add worker and bot services to Compose | Developer 5 | 6 h | Day 3 | Infrastructure | HBS-16, HBS-17 |
| HBS-21 | Create Payment model and test Stripe session | Developer 6 | 3 h | Day 1 | Payments | HBS-09 |
| HBS-22 | Implement payment amount and session helper | Developer 6 | 5 h | Day 2 | Payments | HBS-21 |
| HBS-23 | Connect payments to booking flows | Developer 6 | 4 h | Day 2 | Payments | HBS-13, HBS-15, HBS-16, HBS-22 |
| HBS-24 | Add Stripe success/cancel URLs, tests, docs | Developer 6 | 3 h | Day 3 | Payments | HBS-22 |

## Card description

Keep descriptions short:

```text
Owner: Developer N
Estimate: N h
Depends on: HBS-XX or None
```

Tests and documentation are part of the estimate. Every PR must be approved by
two teammates. The project target is at least 60% test coverage.

## Git workflow

- `main` contains the stable sprint result.
- `develop` is the integration branch for the team.
- Create `feature/HBS-XX-short-name` from the latest `develop`.
- Open feature pull requests into `develop`.
- Open the final release pull request from `develop` into `main`.
- Link every pull request to its Trello card.

# Virtuous CRM+ API: Campaigns, projects & events endpoints
Based on Virtuous CRM+ OpenAPI spec (2026), retrieved 2026-08-31.

All endpoints below share the base host `https://api.virtuoussoftware.com` and the `/api` base path. Every request needs a Bearer access token in the `Authorization` header – see `crm-fundamentals.md` for how to obtain and refresh one. Campaigns, communications, and segments organize outbound fundraising (a campaign holds communications, each communication holds segments), while projects are the destinations that receive gift allocations through gift designations – see `crm-concepts.md` for the fund, campaign, and designation model.

This domain covers 69 operations across nine resources: Campaign, Communication, Segment, Project, ProjectNote, ProjectRole, ProjectExpense, Event, and EventAttendee.

---

## Quick reference

### Campaign (4)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/Campaign/GetStepsByCampaignId/{campaignId}` | List the steps of a multi-touch campaign, in run order. |
| POST | `/api/Campaign/Query` | Query campaigns by conditions; max `take` 1,000. |
| GET | `/api/Campaign/QueryOptions` | List the fields, operators, and values valid in a campaign query. |
| GET | `/api/Campaign/{campaignId}` | Get one campaign, including date range and giving, new-giver, and total-gift goals. |

### Communication (7)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Communication` | Create a communication (one mailing, email, or call) within a campaign. |
| GET | `/api/Communication/ByCampaign/{campaignId}` | List the communications of a campaign; filter by name, page with skip/take. |
| GET | `/api/Communication/ChannelTypes` | List valid channel types (Mail, Email, Phone). Configured in CRM. |
| GET | `/api/Communication/CommunicationTypes` | List valid communication types (Appeal, Newsletter, Acknowledgement). Configured in CRM. |
| POST | `/api/Communication/Query` | Query communications by conditions; max `take` 1,000. |
| GET | `/api/Communication/QueryOptions` | List the fields, operators, and values valid in a communication query. |
| GET | `/api/Communication/{communicationId}` | Get one communication, including its channel, type, goal, campaign, and project. |

### Segment (6)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Segment` | Create a segment (the audience for one version of an appeal) within a communication. |
| GET | `/api/Segment/ByContact/{contactId}` | List the segments a contact belongs to; page with skip/take. |
| GET | `/api/Segment/Code/{segmentCode}` | Get one segment by its code (used to match gifts back to an appeal). |
| POST | `/api/Segment/Search` | Search segments by name or code; page with skip/take. |
| GET | `/api/Segment/{segmentId}` | Get one segment, including code, communication, campaign, count, and cost. |
| PUT | `/api/Segment/{segmentId}` | Update a segment (full model required; omitted fields are cleared). |

### Project (12)

| Method | Path | Purpose |
| --- | --- | --- |
| PATCH | `/api/Project` | Bulk update projects; send only `id` plus the changed fields per project. |
| POST | `/api/Project` | Create a project that gifts can be designated to; Virtuous assigns the code. |
| GET | `/api/Project/Code/{projectCode}` | Get one project by its code. |
| GET | `/api/Project/CustomFields` | List enabled custom fields for the Project object. |
| POST | `/api/Project/Query` | Query projects by conditions; max `take` 1,000. |
| GET | `/api/Project/QueryOptions` | List all query options for projects. |
| POST | `/api/Project/Search` | Search projects by name or code; page with skip/take. |
| GET | `/api/Project/Types` | List valid project types (Program, Fund, Event). Configured in CRM. |
| GET | `/api/Project/{projectId}` | Get the full project record: code, type, balances, need, and giving. |
| PUT | `/api/Project/{projectId}` | Update a project (full model required; omitted fields are cleared). |
| PUT | `/api/Project/{projectId}/Balance` | Set the project's beginning and current balances. |
| PUT | `/api/Project/{projectId}/Status` | Temporarily change inventory status for a window, then restore it. |

### ProjectNote (6)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/ProjectNote` | Create a note on a project. |
| GET | `/api/ProjectNote/ByProject/{projectId}` | List the notes on a project; page with skip/take. |
| GET | `/api/ProjectNote/Types` | List valid project-note types. Configured in CRM. |
| DELETE | `/api/ProjectNote/{noteId}` | Delete a project note (cannot be undone). |
| GET | `/api/ProjectNote/{noteId}` | Get one project note. |
| PUT | `/api/ProjectNote/{noteId}` | Update a project note (full model required; omitted fields are cleared). |

### ProjectRole (7)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/ProjectRole` | Give a contact a role on a project (sponsor, beneficiary, staff lead). |
| GET | `/api/ProjectRole/ByContact/{contactId}` | List the projects a contact has a role on; page with skip/take. |
| GET | `/api/ProjectRole/ByProject/{projectId}` | List the contacts who have a role on a project; page with skip/take. |
| GET | `/api/ProjectRole/Types` | List valid project-role types; page with skip/take. Configured in CRM. |
| DELETE | `/api/ProjectRole/{projectRoleId}` | Remove a contact's role on a project. |
| GET | `/api/ProjectRole/{projectRoleId}` | Get one project role (contact, project, role type). |
| PUT | `/api/ProjectRole/{projectRoleId}` | Change the role type on an existing project role. |

### ProjectExpense (5)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/ProjectExpense` | List expenses on a project (by `projectId` or `projectCode`); filter and page. |
| POST | `/api/ProjectExpense` | Record one expense against a project. |
| POST | `/api/ProjectExpense/Batch` | Record many project expenses in one call. |
| GET | `/api/ProjectExpense/{projectExpenseId}` | Get one project expense. |
| PUT | `/api/ProjectExpense/{projectExpenseId}` | Update a project expense (cannot move it to another project). |

### Event (19)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/Event` | List all events with invite, RSVP, attendance, and giving totals; page with skip/take. |
| POST | `/api/Event` | Create an event you can invite contacts to and record attendance against. |
| GET | `/api/Event/CustomFields` | List enabled custom fields for the Event object. |
| POST | `/api/Event/Query` | Query events by conditions; max `take` 1,000. |
| GET | `/api/Event/QueryOptions` | List the fields, operators, and values valid in an event query. |
| GET | `/api/Event/Search` | Find events whose name matches a filter (type-ahead lookup). |
| GET | `/api/Event/Types` | List valid event types (Gala, Golf Tournament, Open House). Configured in CRM. |
| DELETE | `/api/Event/{eventId}` | Delete an event, its attendees, and its event contacts; gifts stay on contacts. |
| GET | `/api/Event/{eventId}` | Get one event, including location, schedule, and totals. |
| PUT | `/api/Event/{eventId}` | Update an event (full model required; omitted fields are cleared). |
| GET | `/api/Event/{eventId}/Attendees` | List the individuals invited to an event with RSVP and attendance; page with skip/take. |
| POST | `/api/Event/{eventId}/Attendees` | Invite an individual to the event. |
| DELETE | `/api/Event/{eventId}/Attendees/{eventAttendeeId}` | Remove an attendee (the contact is not affected). |
| GET | `/api/Event/{eventId}/Attendees/{eventAttendeeId}` | Get one attendee's RSVP, attendance, and invite-email status. |
| PUT | `/api/Event/{eventId}/Attendees/{eventAttendeeId}` | Record an attendee's RSVP, seating, meal, and attendance. |
| GET | `/api/Event/{eventId}/Contacts` | List the individuals working the event (organizers, hosts, staff); page with skip/take. |
| POST | `/api/Event/{eventId}/Contacts` | Add an individual to the event as an organizer or host. |
| DELETE | `/api/Event/{eventId}/Contacts/{eventContactId}` | Remove an individual from the event's organizers. |
| GET | `/api/Event/{eventId}/Contacts/{eventContactId}` | Get one event contact (name, primary phone, primary email). |

### EventAttendee (3)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/EventAttendee/CustomFields` | List enabled custom fields for the Event Attendee object. |
| POST | `/api/EventAttendee/Query` | Query event attendees across events by conditions; max `take` 1,000. |
| GET | `/api/EventAttendee/QueryOptions` | List the fields, operators, and values valid in an event-attendee query. |

---

## How the pieces fit together

Two hierarchies live in this domain, and they meet at the gift.

**The outreach hierarchy** organizes who you ask and how:

```
Campaign  (the fundraising effort, e.g. "Year-End Giving 2024")
  └─ Communication  (one touch: a mailing, email, or call)
       └─ Segment  (the audience for one version of that appeal)
```

A communication carries a `campaignId`; a segment carries a `communicationId`. So a segment belongs to exactly one communication, and that communication belongs to exactly one campaign. Segment codes travel out on response devices and online forms, which is how an incoming gift is matched back to the appeal that produced it.

**The funding hierarchy** organizes what the money pays for:

```
Project  (the fundable purpose, e.g. "Clean Water Initiative")
  └─ GiftDesignation  (how much of a gift goes to that project)
```

A project is what other platforms call a "fund." Gifts do not reference campaigns or projects directly by a single field – a gift carries one or more gift designations, each naming a project (by `projectId`, `projectCode`, or `externalAccountingCode`). A gift becomes part of a campaign indirectly, because the project it funds is grouped under that campaign. See `crm-api-giving.md` for the gift and designation endpoints.

---

## Campaigns

Campaigns are **read-only** through the CRM+ API. The spec exposes a get, a query, a query-options, and a steps endpoint – there is no `POST /api/Campaign`, no `PUT`, and no `DELETE`. If an integration needs a new campaign, direct the nonprofit administrator to create it in the Virtuous UI under **Campaigns**, then reference its projects in gift submissions.

A campaign record has this shape (from `crm-concepts.md`):

```json
{
  "campaignId": 22,
  "name": "Year-End Giving 2024",
  "startDateTimeUtc": "2024-11-01T00:00:00Z",
  "endDateTimeUtc": "2024-12-31T23:59:59Z",
  "givingGoal": 250000,
  "newGiverGoal": 100,
  "totalGiftGoal": 800,
  "isArchived": false
}
```

### Query campaigns

`POST /api/Campaign/Query` takes the shared Virtuous query envelope in its body and `skip`/`take` in the query string.

| Field | Type | Notes |
| --- | --- | --- |
| `groups` | array of objects | Condition groups. Get valid parameters, operators, and values from `GET /api/Campaign/QueryOptions`. |
| `sortBy` | string | Field to sort on. |
| `descending` | string | Sort direction. |

```json
{
  "groups": [
    {
      "conditions": [
        { "parameter": "Name", "operator": "Contains", "value": "Year-End" }
      ]
    }
  ],
  "sortBy": "Name",
  "descending": "false"
}
```

The `parameter`, `operator`, and `value` names above are illustrative. Always call `QueryOptions` first for the exact allowed values – the envelope shape (groups → conditions) is the shared query pattern documented in `crm-fundamentals.md`.

### Campaign steps

`GET /api/Campaign/GetStepsByCampaignId/{campaignId}` returns the steps of a multi-touch campaign in run order. Steps group the communications that make up a campaign plan. Most integrations do not interact with steps directly.

---

## Communications

A communication is one touch in a campaign: a single mailing, email, or call. Create it with `POST /api/Communication`.

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | Communication name. |
| `campaignId` | string | The campaign this communication belongs to. |
| `channelType` | string | Use a value from `GET /api/Communication/ChannelTypes` (Mail, Email, Phone). |
| `communicationType` | string | Use a value from `GET /api/Communication/CommunicationTypes` (Appeal, Newsletter, Acknowledgement). |
| `communicationStep` | string | The campaign step this touch belongs to. |
| `startDateTime` | string | When the communication goes out. |
| `ownerId` | string | Owning user. |
| `givingGoal` | string | Target giving for this touch. |
| `newGiverGoal` | string | Target new givers for this touch. |
| `internalCostEstimate` | string | Estimated in-house cost. |
| `vendorCostEstimate` | string | Estimated vendor cost. |
| `networkReach` | string | Reach for this touch. |

```json
{
  "name": "Year-End Appeal – December Mail Drop",
  "campaignId": "22",
  "channelType": "Mail",
  "communicationType": "Appeal",
  "startDateTime": "2024-12-01T09:00:00",
  "givingGoal": "50000",
  "newGiverGoal": "25",
  "internalCostEstimate": "1200",
  "vendorCostEstimate": "3400",
  "networkReach": "12000"
}
```

Read them back with `GET /api/Communication/ByCampaign/{campaignId}` (supports `filter` by name plus `sortBy`, `descending`, `skip`, `take`), `GET /api/Communication/{communicationId}` for one record, or `POST /api/Communication/Query` for structured filtering. `GET /api/Communication/QueryOptions` lists the valid query fields.

---

## Segments

A segment is the audience for one version of an appeal, created within a communication. Its `code` must be unique because that code is what links inbound gifts back to the appeal.

`POST /api/Segment`:

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | Segment name. |
| `code` | string | Unique segment code. |
| `communicationId` | string | The communication this segment belongs to. |
| `description` | string | Free text. |
| `totalContacts` | string | Size of the audience, used for return reporting. |
| `contactQueryId` | string | The contact query that defines the audience. |
| `costPerContact` | string | Per-contact cost, used for return reporting. |
| `packageCode` | string | Package (creative) code. |
| `packageDescription` | string | Package description. |
| `receiptSegmentId` | string | Related receipt segment. |
| `segmentOrganizerId` | string | Owning organizer. |

```json
{
  "name": "Year-End Appeal – Lapsed Donors",
  "code": "YE24-LAPSED",
  "communicationId": "108",
  "totalContacts": "4200",
  "contactQueryId": "551",
  "costPerContact": "0.78",
  "packageCode": "YE24-PKG-A"
}
```

`PUT /api/Segment/{segmentId}` updates a segment with the same fields **except** `communicationId` – you cannot move a segment to a different communication through the update. As with other Virtuous updates, the full model is required and any omitted field is cleared.

### Segment membership

`GET /api/Segment/ByContact/{contactId}` lists the segments a contact belongs to, so you can see which appeals included that person. There is no endpoint here that adds or removes a single contact from a segment directly – membership follows from the segment's `contactQueryId` audience. Find segments with `POST /api/Segment/Search` (by name or code), `GET /api/Segment/Code/{segmentCode}` (exact code, useful when matching gifts back to an appeal), or `GET /api/Segment/{segmentId}`.

---

## Projects

A project is a fundable purpose – the destination a gift designation points at, and the "fund" equivalent from other platforms. Create one with `POST /api/Project`. Virtuous assigns the `projectCode` and returns it in the response, so do not send a code on create.

`POST /api/Project` body (query param: `disableWebhookUpdates`):

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | Project name. |
| `revenueAccountingCode` | string | Revenue account code. |
| `inventoryStatus` | string | Inventory status. |
| `type` | string | Use a value from `GET /api/Project/Types` (Program, Fund, Event). |
| `location` | string | Project location. |
| `onlineDisplayName` | string | Name shown on public donation forms. |
| `description` | string | Free text. |
| `externalAccountingCode` | string | Accounting-system code (often the GL account number) used for reconciliation. |
| `durationType` | string | Duration model. |
| `startDate` | string | Start date. |
| `endDate` | string | End date. |
| `financialNeedAmount` | string | Fundraising target. |
| `financialNeedType` | string | Type of financial need. |
| `financialNeedFrequency` | string | How often the need recurs. |
| `isPublic` | string | Whether the project shows in the org-wide project list. |
| `isActive` | string | Whether the project accepts new designations. |
| `isAvailableOnline` | string | Whether the project can be designated to from a public form. |
| `isLimitedToFinancialNeed` | string | Cap giving at the need amount. |
| `isTaxDeductible` | string | Whether designations are tax-deductible (affects receipts). |
| `treatAsAccountsPayable` | string | Accounting behavior flag. |
| `isRestrictedToGiftSpecifications` | string | Restrict to gift specifications. |
| `parentId` | string | Parent project ID for a sub-project (rolls up to the parent). |
| `beginningBalance` | string | Starting balance. |
| `currentBalance` | string | Current balance. |
| `enableSync` | string | Keep the project in step with your accounting system. |
| `customFields` | array of objects | Custom-field values (see `GET /api/Project/CustomFields`). |

```json
{
  "name": "Clean Water Initiative",
  "onlineDisplayName": "Clean Water",
  "type": "Program",
  "location": "International",
  "externalAccountingCode": "5101-001",
  "financialNeedAmount": "100000",
  "isPublic": "true",
  "isActive": "true",
  "isAvailableOnline": "true",
  "isTaxDeductible": "true",
  "enableSync": "true"
}
```

The response includes the assigned `projectCode` (for example `"CLEAN-WATER"`) plus giving totals such as `currentBalance`, `lifeToDateGiving`, and `lifeToDateGiftCount`.

### Update a project

- `PUT /api/Project/{projectId}` – update one project. The full model is required; any omitted field is cleared. Accepts the same body as create plus the `disableWebhookUpdates` query param.
- `PATCH /api/Project` – bulk update. Unlike the single-project `PUT`, this is a true patch: send an **array** of objects, each with `id` plus only the fields that change (`name`, `projectCode`, `onlineDisplayName`, `description`, `financialNeedAmount`, `beginningBalance`, `currentBalance`, `type`, `startDate`, `endDate`, `customFields`). Use it whenever more than one project changes.

```json
[
  { "id": "311", "name": "Clean Water Initiative (2025)" },
  { "id": "312", "currentBalance": "5000" }
]
```

Note the asymmetry: create does not accept `projectCode` (Virtuous assigns it), but the bulk `PATCH` lists `projectCode` among its updatable fields.

- `PUT /api/Project/{projectId}/Balance` – set `beginningBalance` and `currentBalance` directly. Use it to seed balances on first sync or to correct them. Gifts and expenses are not changed.
- `PUT /api/Project/{projectId}/Status` – temporarily change inventory status. Pass `inventoryStatus` and `durationMinutes` as query params; the status reverts after the window. Use it to hold a project open or closed while a campaign is live, without a permanent change.

### Read projects

| Endpoint | When to use |
| --- | --- |
| `GET /api/Project/{projectId}` | Look up one project by Virtuous ID. |
| `GET /api/Project/Code/{projectCode}` | Look up by code – useful when your platform stores the code rather than the ID. |
| `POST /api/Project/Query` | Filtered paginated retrieval. Filter to `isActive: true` and `isPublic: true` for the set valid for new designations. Max `take` 1,000. |
| `POST /api/Project/Search` | Fuzzy search by name or code; body `{ "search": "water" }`; page with skip/take. |
| `GET /api/Project/Types` | List valid project types. |
| `GET /api/Project/CustomFields` | List enabled project custom fields. |

The spec advises against polling `Query` for new or updated projects – use a project webhook instead.

---

## Project notes

Notes record updates, decisions, or conversations about a project. Create with `POST /api/ProjectNote`.

| Field | Type | Notes |
| --- | --- | --- |
| `projectId` | string | The project the note is on. |
| `type` | string | Use a value from `GET /api/ProjectNote/Types`. |
| `note` | string | The note body. |
| `important` | string | Flag as important. |
| `private` | string | Flag as private. |
| `contactId` | string | Tie the note to the contact it concerns. |

Read with `GET /api/ProjectNote/ByProject/{projectId}` (page with skip/take) or `GET /api/ProjectNote/{noteId}`. Update with `PUT /api/ProjectNote/{noteId}` (`type`, `note`, `important`, `private`, `contactId`; full model required). Delete with `DELETE /api/ProjectNote/{noteId}` – this cannot be undone.

---

## Project roles

A project role gives a contact a standing on a project – a sponsor, a beneficiary, or a staff lead. Create with `POST /api/ProjectRole`.

| Field | Type | Notes |
| --- | --- | --- |
| `projectDesignationId` | string | The project designation the role attaches to. |
| `contactId` | string | The contact getting the role. |
| `projectRoleTypeId` | string | Use a value from `GET /api/ProjectRole/Types`. |

Note that create references `projectDesignationId`, whereas the list endpoint is keyed by project (`/ByProject/{projectId}`). List roles by project with `GET /api/ProjectRole/ByProject/{projectId}` or by contact with `GET /api/ProjectRole/ByContact/{contactId}` (both page with skip/take). Get one with `GET /api/ProjectRole/{projectRoleId}`.

`PUT /api/ProjectRole/{projectRoleId}` changes only the `projectRoleTypeId`; the contact and project stay fixed. To move a role to a different contact, delete it (`DELETE /api/ProjectRole/{projectRoleId}`) and create a new one.

---

## Project expenses

Expenses record the cost of the work a project funds, so cost can be reported next to giving. Create with `POST /api/ProjectExpense`.

| Field | Type | Notes |
| --- | --- | --- |
| `projectId` | string | The project the expense posts against. |
| `expenseAmount` | string | Amount. |
| `expenseDate` | string | Date incurred. |
| `accountingCode` | string | Code the expense posts to in your accounting system. |
| `expenseDescription` | string | Free text. |

For periodic syncs from an accounting system, use `POST /api/ProjectExpense/Batch` – send `projectExpenses` as an array of objects each shaped like a single create body, instead of one request per expense.

List with `GET /api/ProjectExpense`, identifying the project by `projectId` **or** `projectCode`. It also accepts `filter` (narrow by description or accounting code), `take`, and `count`. This list uses `take` and `count` rather than the `skip`/`take` paging of most other lists. Get one with `GET /api/ProjectExpense/{projectExpenseId}`. Update with `PUT /api/ProjectExpense/{projectExpenseId}` (`expenseAmount`, `expenseDate`, `accountingCode`, `expenseDescription`) – an expense cannot be moved to a different project.

---

## Events and attendees

An event is something you invite contacts to and record attendance and giving against. Create with `POST /api/Event`.

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | Event name. |
| `eventType` | string | Use a value from `GET /api/Event/Types` (Gala, Golf Tournament, Open House). |
| `startDateTime` | string | Start, in the event's local time. |
| `endDateTime` | string | End, in the event's local time. |
| `timeZone` | string | Time zone for the local start/end. |
| `communicationId` | string | Communication the event is tied to. |
| `locationName` | string | Venue name. |
| `description` | string | Free text. |
| `specialInstructions` | string | Instructions for staff or guests. |
| `inviteOnly` | string | Whether attendance is invite-only. |
| `rsvpRequired` | string | Whether an RSVP is required. |
| `tables` | array of strings | Seating tables. |
| `meals` | array of strings | Catering / meal options. |
| `address1`, `address2`, `city`, `state`, `postal`, `country` | string | Venue address. |
| `eventbriteId` | string | Linked Eventbrite event. |
| `customFields` | array of objects | Custom-field values (see `GET /api/Event/CustomFields`). |

```json
{
  "name": "Spring Gala 2025",
  "eventType": "Gala",
  "startDateTime": "2025-04-12T18:00:00",
  "endDateTime": "2025-04-12T22:00:00",
  "timeZone": "Eastern Standard Time",
  "locationName": "Grand Ballroom",
  "city": "Atlanta",
  "state": "GA",
  "inviteOnly": "true",
  "rsvpRequired": "true",
  "tables": ["Table 1", "Table 2"],
  "meals": ["Chicken", "Vegetarian"]
}
```

`PUT /api/Event/{eventId}` updates an event with the same body; the full model is required and omitted fields are cleared. `DELETE /api/Event/{eventId}` removes the event, its attendees, and its event contacts, but gifts recorded against it stay on their contacts.

### Reading events

| Endpoint | When to use |
| --- | --- |
| `GET /api/Event` | List all events with totals; page with skip/take. |
| `GET /api/Event/{eventId}` | Get one event. |
| `GET /api/Event/Search` | Type-ahead lookup by name (`filter`). |
| `POST /api/Event/Query` | Structured filtering; max `take` 1,000. `GET /api/Event/QueryOptions` lists valid fields. |

### Attendees vs. event contacts

An event has two kinds of people, and they use different endpoints:

- **Attendees** are the guests you invite. Add with `POST /api/Event/{eventId}/Attendees`, sending `contactIndividualId` (and optional `customFields`).
- **Event contacts** are the organizers, hosts, and staff working the event. Add with `POST /api/Event/{eventId}/Contacts`, sending `contactIndividualId`.

After inviting an attendee, record their participation with `PUT /api/Event/{eventId}/Attendees/{eventAttendeeId}`:

| Field | Type | Notes |
| --- | --- | --- |
| `invited` | string | Whether they were invited. |
| `rsvp` | string | RSVP status. |
| `rsvpResponse` | string | RSVP response detail. |
| `attended` | string | Whether they attended. |
| `schedule` | string | Schedule assignment. |
| `table` | string | Seating table. |
| `meal` | string | Meal choice. |
| `customFields` | array of objects | Custom-field values. |

List attendees with `GET /api/Event/{eventId}/Attendees` and event contacts with `GET /api/Event/{eventId}/Contacts` (both page with skip/take). Get or delete a single one by its ID. Deleting either removes the event record only; the underlying contact is not affected.

### Querying attendees across events

The `EventAttendee` resource queries attendees across all events, rather than within one event. `POST /api/EventAttendee/Query` takes the shared query envelope (`groups`, `sortBy`, `descending`) with `skip`/`take`; `GET /api/EventAttendee/QueryOptions` lists valid fields; `GET /api/EventAttendee/CustomFields` lists enabled custom fields.

---

## Gotchas and patterns

**Campaign, communication, and segment nest one inside the next.** A segment names a `communicationId`; a communication names a `campaignId`. Campaigns are read-only over the API, so an integration can read this outreach structure and attach gifts to it, but it cannot create the campaign itself – that is a UI task. There is no create-campaign or create-communication-step write path in this spec.

**A gift never points at a campaign or project with a single field.** Money flows Gift → GiftDesignation → Project, and a project is grouped under a campaign. To fund a project, put a designation on the gift naming the project by `projectCode`, `projectId`, or `externalAccountingCode`; designation amounts must sum to the gift amount or the gift is rejected. See `crm-api-giving.md` and `crm-concepts.md`.

**Prefer `projectCode` as the integration anchor.** It is human-readable, can be configured to match your platform's fund identifier, and stays stable across migrations more reliably than the numeric `id`. `externalAccountingCode` is the bridge to an accounting system. Look projects up with `GET /api/Project/Code/{projectCode}`, and designate gifts by code.

**Respect `isActive` before designating.** An inactive project still holds historical gifts but rejects new designations (a `400`/`422`). The defensive pattern is to query active, public projects at setup (`POST /api/Project/Query` filtered to `isActive: true`, `isPublic: true`) and let the customer map to them.

**Projects accumulate dependencies and are not deletable here.** A project carries balances, giving totals (`lifeToDateGiving`, `lifeToDateGiftCount`), expenses, notes, and roles. There is no `DELETE /api/Project/{projectId}` in this spec, so projects are long-lived – deactivate with `isActive` rather than expecting to remove one. Sub-projects roll their giving up to the parent via `parentId`; designate to the most specific project and Virtuous handles the rollup. To count expenses on a project, use the `count` param on `GET /api/ProjectExpense`.

**Full-model `PUT` clears omitted fields; `PATCH /api/Project` does not.** Every single-record update in this domain (project, segment, event, attendee, note, expense, role) requires the entire model – leaving a field out erases its value. The exception is `PATCH /api/Project`, which is a genuine partial update: send `id` plus only the changed fields. When more than one project changes, use the bulk `PATCH`.

**Paging is `skip`/`take`, with one exception.** Query and list endpoints take `skip` and `take` in the query string; the max `take` on any `Query` endpoint is 1,000. To read a full set, page until a call returns fewer than `take` rows. The outlier is `GET /api/ProjectExpense`, which uses `take` and `count` and has no `skip`.

**Always build query bodies from `QueryOptions`.** Each queryable resource (Campaign, Communication, Event, EventAttendee, Project) has a matching `QueryOptions` endpoint that returns the fields, operators, and values its `Query` accepts. The body envelope (`groups` → `conditions`, plus `sortBy` and `descending`) is shared across the API; the valid parameter names inside it are per-resource. Do not guess them.

**`disableWebhookUpdates` suppresses project webhooks.** Both `POST /api/Project` and `PUT /api/Project/{projectId}` accept it as a query param – set it when a write should not fire project webhook notifications (for example, an echo of a change that originated in your system).

---

## Related skills

- `crm-concepts.md` – the fund, campaign, designation, and gift model this domain sits inside.
- `crm-api-giving.md` – gifts and gift designations that reference these projects and segments.
- `crm-api-contacts.md` – the contacts invited to events, given project roles, and grouped into segments.
- `crm-workflows.md` – end-to-end recipes that combine these endpoints (for example, recording an event gift).
- `crm-fundamentals.md` – Bearer authentication, the shared query envelope, and paging conventions.
- `crm-api-system.md` – custom-field definitions, webhooks, and other system-level endpoints.

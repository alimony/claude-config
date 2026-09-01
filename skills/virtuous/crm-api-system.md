# Virtuous CRM+ API: System & supporting endpoints
Based on Virtuous CRM+ OpenAPI spec (2026), retrieved 2026-08-31.

All requests go to host `https://api.virtuoussoftware.com` with base path `/api` (the one exception is the auth token endpoint, which lives at `/Token`, with no `/api` prefix). This file is the endpoint reference for the cross-cutting resources that support every other CRM+ domain: the OAuth access token, organization and permission lookups, webhook subscription management, tasks, email send and lists, and global search. It also documents the Reminder endpoints (flagged deprecated below) and the Volunteer and VolunteerOpportunity endpoints, which belong to the Volunteer product but are exposed inside the CRM+ spec.

## Base URL and authentication

- **Host:** `https://api.virtuoussoftware.com`
- **Base path:** `/api` for every resource except `POST /Token`, which sits at the root.
- **Auth header:** send `Authorization: Bearer <access_token>` on every `/api` call. Get the token from `POST /Token` (see below).
- **Update semantics:** `PUT` endpoints replace the whole object. Omitting a property clears its value, so read the record first, then send the full model back with your change applied.

## Quick reference

Every endpoint in the digest, grouped by resource. `OAuth` = open authorization; `CRUD` = create, read, update, delete.

### Token (1)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/Token` | Exchange credentials (or a refresh token) for an OAuth access token. Note: no `/api` prefix. |

### Organization (3)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/Organization` | List the organizations the authenticated user belongs to. |
| GET | `/api/Organization/Current` | Get the organization the user is currently working in. |
| PUT | `/api/Organization/Switch` | Switch the organization used for subsequent requests. |

### Permission (1)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/Permission` | List the module/action permissions granted to the user or API key. |

### Webhook (5)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Webhook` | Create a webhook subscription for the events you select. |
| GET | `/api/Webhook/{webhookId}` | Get a single webhook, including its events and signing secret. |
| PUT | `/api/Webhook/{webhookId}` | Update a webhook's URL, secret, or event subscriptions. |
| PUT | `/api/Webhook/{webhookId}/Active` | Activate or pause delivery via the `active` query parameter. |
| DELETE | `/api/Webhook/{webhookId}` | Delete a webhook and stop all delivery. |

### Task (4)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Task` | Create a task with a due date, optionally tied to a contact. |
| POST | `/api/Task/Query` | Query tasks by condition groups. Max `take` is 1,000. |
| GET | `/api/Task/QueryOptions` | Get the fields, operators, and values for a task query. |
| GET | `/api/Task/Types` | List the task types that can be set on a task. |

### Email (2)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Email/Search` | Find emails by name or subject; returns the `emailId` used to send. |
| POST | `/api/Email/Send` | Send an existing Virtuous email to a list of contacts. |

### EmailList (2)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/EmailList` | Queue a bulk add of individuals to one or more email lists (async). |
| POST | `/api/EmailList/Search` | Find email lists by name; returns the list id used to add individuals. |

### Search (1)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Search` | Global search across contacts, individuals, and other entities. |

### Reminder (16) – deprecated

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Reminder` | Create a one-time reminder for a user to follow up. |
| GET | `/api/Reminder/Active` | List the user's due, unresolved reminders. |
| GET | `/api/Reminder/ByContact/{contactId}` | List a contact's unresolved reminders, due or not. |
| GET | `/api/Reminder/ByContact/{contactId}/Active` | List a contact's due, unresolved reminders. |
| GET | `/api/Reminder/ByContact/{contactId}/Inactive` | List a contact's completed or dismissed reminders. |
| PUT | `/api/Reminder/Completed/{id}` | Mark a reminder complete and file a contact note. |
| PUT | `/api/Reminder/Dismissed/{id}` | Dismiss a reminder without a note. |
| GET | `/api/Reminder/Saved` | List saved recurring and milestone reminder definitions. |
| POST | `/api/Reminder/Saved/Milestone` | Create a milestone reminder rule. |
| PUT | `/api/Reminder/Saved/Milestone/{id}` | Update a milestone reminder rule. |
| POST | `/api/Reminder/Saved/Recurring` | Create a recurring reminder rule. |
| PUT | `/api/Reminder/Saved/Recurring/{id}` | Update a recurring reminder rule. |
| GET | `/api/Reminder/Type/Milestone` | List the milestone types a milestone reminder can watch. |
| GET | `/api/Reminder/Type/Reminder` | List the reminder types. |
| GET | `/api/Reminder/Type/ReminderFrequency` | List the recurring frequencies (for example Monthly, Quarterly). |
| GET | `/api/Reminder/Type/ReminderSource` | List the reminder source types. |

### Volunteer (3) – Volunteer product

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Volunteer/Query` | Query volunteers by condition groups. |
| GET | `/api/Volunteer/QueryOptions` | Get the fields, operators, and values for a volunteer query. |
| GET | `/api/Volunteer/Search` | Find an existing volunteer signup across all opportunities. |

### VolunteerOpportunity (21) – Volunteer product

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/VolunteerOpportunity` | List all volunteer opportunities; `filter` narrows by name. |
| POST | `/api/VolunteerOpportunity` | Create a volunteer opportunity. |
| GET | `/api/VolunteerOpportunity/CustomFields` | List enabled custom fields for the opportunity object. |
| POST | `/api/VolunteerOpportunity/Query` | Query opportunities by condition groups. |
| GET | `/api/VolunteerOpportunity/QueryOptions` | Get the fields, operators, and values for an opportunity query. |
| GET | `/api/VolunteerOpportunity/{volunteerOpportunityId}` | Get a single opportunity. |
| PUT | `/api/VolunteerOpportunity/{volunteerOpportunityId}` | Update an opportunity. |
| DELETE | `/api/VolunteerOpportunity/{volunteerOpportunityId}` | Delete an opportunity (only if it has no organizers or volunteers). |
| GET | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Organizers` | List the opportunity's organizers. |
| POST | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Organizers` | Add an individual as an organizer. |
| GET | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Organizers/{volunteerOrganizerId}` | Get a single organizer. |
| DELETE | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Organizers/{volunteerOrganizerId}` | Remove an organizer. |
| GET | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Volunteers` | List volunteers signed up for the opportunity. |
| POST | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Volunteers` | Sign an individual up to serve. |
| GET | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Volunteers/{volunteerId}` | Get a single volunteer on the opportunity. |
| DELETE | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Volunteers/{volunteerId}` | Remove a volunteer and their attendance on the opportunity. |
| GET | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Volunteers/{volunteerId}/Attendance` | List attendance logged for the volunteer. |
| POST | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Volunteers/{volunteerId}/Attendance` | Log a shift for the volunteer. |
| GET | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Attendance/{volunteerAttendanceId}` | Get a single attendance record. |
| PUT | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Attendance/{volunteerAttendanceId}` | Correct a logged shift. |
| DELETE | `/api/VolunteerOpportunity/{volunteerOpportunityId}/Attendance/{volunteerAttendanceId}` | Delete an attendance record and its hours. |

## Token (POST /Token)

This is the OAuth token exchange and the entry point for every other call. It is the only endpoint at the root path, `/Token`, not under `/api`. Send the body as `application/x-www-form-urlencoded`.

**Password grant** exchanges a username and password for a token:

```http
POST /Token HTTP/1.1
Host: api.virtuoussoftware.com
Content-Type: application/x-www-form-urlencoded

grant_type=password&username=USER%40EXAMPLE.COM&password=URL_ENCODED_PASSWORD
```

**Refresh grant** exchanges a saved refresh token for a fresh access token, so you avoid re-sending credentials:

```http
POST /Token HTTP/1.1
Host: api.virtuoussoftware.com
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=REFRESH_TOKEN
```

| Body field | When to send | Notes |
| --- | --- | --- |
| `grant_type` | Always | `password` or `refresh_token`. |
| `username` | Password grant | URL-encode it. |
| `password` | Password grant | URL-encode it. |
| `refresh_token` | Refresh grant | A refresh token returned by an earlier response. |

Lifetimes from the digest: access tokens last 15 days; refresh tokens last 365 days. Store the refresh token and use the refresh grant to renew access without a password.

Once you have a token, authenticate every `/api` request with `Authorization: Bearer <access_token>`.

**Two-factor authentication:** the digest notes that when the user has two-factor authentication enabled, the first request returns a different response (the digest text is truncated at this point and does not show the full challenge/verification flow). See `crm-fundamentals.md` for the complete authentication and two-factor walkthrough.

> Ambiguity: the digest describes the request body and token lifetimes but does not enumerate the response fields. A standard OAuth password grant returns an access token and a refresh token (the digest confirms both exist); treat exact response field names as unconfirmed here and verify against `crm-fundamentals.md`.

## Organization and permissions

Use these to learn which database you are pointed at, move between databases, and check access before a call.

### GET /api/Organization – list my organizations

Returns each organization the user belongs to, with its identifier, time zone, culture, and whether the user is an administrator. Use `organizationId` to tell databases apart in a multi-tenant integration, and `organizationUserId` with the switch endpoint below.

### GET /api/Organization/Current – get current organization

Returns the organization your requests currently read and write, plus its time zone and culture (use these to format dates and currency correctly).

### PUT /api/Organization/Switch – switch current organization

Changes the active organization for subsequent requests.

```json
{ "organizationUserId": "the-target-organization-user-id" }
```

| Body field | Type | Notes |
| --- | --- | --- |
| `organizationUserId` | string | From `GET /api/Organization`. Identifies the target organization for this user. |

### GET /api/Permission – get my permissions

Returns the permissions granted to the user or API key as module/action pairs, each with whether it is allowed. Call it to check access before a request the key may not be permitted to make.

## Webhook management

Webhooks push real-time notifications to a URL you control when records change, so you avoid polling. See `crm-webhooks.md` for the full lifecycle: event types, signature verification, retry behavior, idempotency, and local testing.

### POST /api/Webhook – create a webhook

Subscribes a payload URL to the events you select. Set `secret` to a value you generate; use it to verify the signature on each delivery.

```bash
curl -X POST https://api.virtuoussoftware.com/api/Webhook \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payloadUrl": "https://your-integration.example.com/virtuous/webhook",
    "secret": "your-randomly-generated-secret",
    "contactCreate": true,
    "contactUpdate": true,
    "giftCreate": true,
    "giftUpdate": true,
    "active": true
  }'
```

Body fields (the same set is sent on create and update):

| Field | Type | Purpose |
| --- | --- | --- |
| `payloadUrl` | string | HTTPS URL that receives event POSTs. |
| `secret` | string | Shared secret you provide, used for signature verification. |
| `active` | boolean | `true` delivers events; `false` drops them (they are not queued). |
| `contactCreate`, `contactUpdate` | boolean | Contact lifecycle events. |
| `giftCreate`, `giftUpdate`, `giftDelete` | boolean | Gift lifecycle events. |
| `projectCreate`, `projectUpdate`, `projectDelete` | boolean | Project lifecycle events. |
| `formSubmission` | boolean | Form submission events from Virtuous-hosted forms. |
| `contactNoteCreate`, `contactNoteUpdate`, `contactNoteDelete` | boolean | ContactNote lifecycle events. |
| `eventCreate`, `eventUpdate`, `eventDelete` | boolean | Event (calendar/program event) lifecycle events. |

The create response echoes the subscription, including an integer `id`. Store that `id` – you need it for every management call, and the spec has no list-all endpoint (see the note below).

### GET /api/Webhook/{webhookId} – get a webhook

Returns one subscription: payload URL, signing secret, active flag, and subscribed events.

### PUT /api/Webhook/{webhookId} – update a webhook

Updates the payload URL, secret, and event subscriptions. This is a full replace: send every field you want to keep, including the payload URL, secret, and any event flags already enabled, or you will disable them. Rotate a secret by sending the same object with a new `secret`; the new value takes effect on the next delivery.

### PUT /api/Webhook/{webhookId}/Active – toggle active state

Activates or pauses delivery in one call, without changing the URL or event selections.

| Query param | Values |
| --- | --- |
| `active` | `true` resumes delivery; `false` pauses it. |

### DELETE /api/Webhook/{webhookId} – delete a webhook

Deletes the subscription and stops all delivery. To pause without losing the configuration, set it inactive instead.

> Two gaps to plan around, both confirmed in the webhooks overview: the CRM+ spec has **no endpoint to list all webhook subscriptions** (persist each `id` from create), and it has **no webhook delivery-log endpoint**. If you need delivery history, record it on your own receiver.

## Tasks

Tasks are dated to-dos, optionally attached to a contact. The Query endpoint uses the same condition-group pattern as the other query endpoints in the API.

### POST /api/Task – create a task

Creates a task with a due date, optionally tied to a contact. Use `GET /api/Task/Types` for the allowed `taskType` values.

> The digest does not enumerate the create body fields. Discover the accepted fields and values with `GET /api/Task/QueryOptions` and `GET /api/Task/Types` before building the request.

### POST /api/Task/Query – query tasks

Returns tasks matching your condition groups. Page with `skip` and `take` query parameters; the maximum `take` is 1,000. If requests time out, lower `take`.

| Query param | Purpose |
| --- | --- |
| `skip` | Number of results to skip. |
| `take` | Page size, up to 1,000. |

Call `GET /api/Task/QueryOptions` first to learn which fields, operators, and values the body accepts. (The digest lists the query parameters but does not spell out the request body shape for tasks.)

### GET /api/Task/QueryOptions – get task query options

Returns the fields, operators, and values available when you build a task query.

### GET /api/Task/Types – list task types

Returns the task types you can set on a task.

## Email and email lists

These endpoints send an existing Virtuous email and manage list membership. They do not compose email content; the email must already exist in Virtuous.

### POST /api/Email/Search – search emails

Finds emails whose name or subject matches your term, fully or partially. Use it to get the `emailId` for a send. Page with `skip` and `take` query parameters.

```json
{ "search": "year-end appeal" }
```

### POST /api/Email/Send – send an email

Sends an existing Virtuous email to the contacts you list.

```json
{
  "emailId": "the-email-id-from-search",
  "contactIds": ["1001", "1002"],
  "personalizations": [],
  "sections": ""
}
```

| Body field | Type | Purpose |
| --- | --- | --- |
| `emailId` | string | The email to send; get it from `POST /api/Email/Search`. |
| `contactIds` | array of string | Contacts to send to. |
| `personalizations` | array of object | Per-recipient personalization values. |
| `sections` | string | Section content for the email. |

### POST /api/EmailList – add individuals to an email list

Queues a bulk add of individuals to one or more lists. This is asynchronous: it returns an `Accepted` response, and the queue can take up to 4 hours to finish. The digest advises against using it for a single individual; batch your adds instead.

```json
{
  "emailListIds": ["55"],
  "contactIndividualIds": ["9001", "9002", "9003"]
}
```

| Body field | Type | Purpose |
| --- | --- | --- |
| `emailListIds` | array of string | Lists to add people to. |
| `contactIndividualIds` | array of string | Individuals to add. |

### POST /api/EmailList/Search – search email lists

Finds lists whose name matches your term. Use it to get the list id for the add endpoint above. Page with `skip` and `take`.

```json
{ "search": "monthly newsletter" }
```

## Global search

### POST /api/Search – search contacts, individuals, or entities

Searches contacts, individuals, and other entities in one call and returns matches grouped by type. It is built for a global search box. For structured filtering on one record type, use that type's own query endpoint instead.

```json
{
  "query": "smith",
  "filterTypes": ["Contact", "ContactIndividual"]
}
```

| Field | Type | Purpose |
| --- | --- | --- |
| `query` | string | The search term. |
| `filterTypes` | array of string | Restrict which record kinds are searched. |
| `skip`, `take` | query params | Page through results. |

## Reminders (deprecated)

**Status: deprecated.** Treat the 16 Reminder endpoints as legacy and avoid building new integrations on them. The digest does not name a replacement resource, so the successor is not confirmed here; the Task endpoints in this same file cover dated, contact-linked follow-ups and are the natural place to look for equivalent behavior. Confirm the migration path in the current documentation before you rely on it.

The endpoints fall into four groups (full paths are in the quick reference above):

- **One-time reminders:** create, list active (yours or by contact), and resolve by completing or dismissing.
- **Saved rules:** milestone and recurring definitions that generate reminders, with create, update, and list.
- **Type lookups:** milestone types, reminder types, frequency types, and source types.

Key request bodies from the digest:

`POST /api/Reminder` (create a one-time reminder):

| Field | Purpose |
| --- | --- |
| `taskType` | The kind of reminder. |
| `message` | The reminder text. |
| `dueDate` | When it comes due. |
| `contactId` | The contact it concerns. |
| `ownerEmail` | The user who receives it. |
| `description` | Longer description. |

`PUT /api/Reminder/Completed/{id}` (complete and file a note): `noteTypeName`, `note`, `timeSpent`, `isImportant`, `isPrivate`.

`POST /api/Reminder/Saved/Milestone` (milestone rule): `name`, `milestoneType`, `threshold`, `ownerEmail`, `description`. Use `GET /api/Reminder/Type/Milestone` for `milestoneType` values.

`POST /api/Reminder/Saved/Recurring` (recurring rule): `taskType`, `message`, `name`, `dueDate`, `contactId`, `reminderFrequency`, `ownerEmail`, `description`. Use `GET /api/Reminder/Type/ReminderFrequency` for `reminderFrequency` values.

The update endpoints (`.../Saved/Milestone/{id}`, `.../Saved/Recurring/{id}`) are full replaces, like other CRM+ updates: send the whole model even to change one property.

## Volunteer product endpoints

**Ownership: these 24 endpoints belong to the Volunteer product, not CRM+ proper, but they are exposed in the CRM+ spec.** They cover volunteer signups, opportunities, organizers, and attendance. If your organization does not use the Volunteer product, expect them to be unavailable.

### Volunteer lookup (3)

- `POST /api/Volunteer/Query` – query volunteers by condition groups; discover options with `GET /api/Volunteer/QueryOptions`.
- `GET /api/Volunteer/QueryOptions` – fields, operators, and values for a volunteer query.
- `GET /api/Volunteer/Search` – find an existing signup across all opportunities. Query parameters: `volunteerOpportunityId`, `volunteerId`, `contactId`, `contactIndividualId`, `emailAddress`, `skip`, `take`. Use it, for example, before recording attendance for a walk-in.

### VolunteerOpportunity (21)

Opportunities are the units of work volunteers sign up for. The endpoints form standard CRUD plus a query pair, with nested Organizers, Volunteers, and Attendance collections (all paths are in the quick reference).

`POST` / `PUT /api/VolunteerOpportunity` body fields:

| Field | Notes |
| --- | --- |
| `name` | Opportunity name. |
| `startDateTime`, `endDateTime` | In the opportunity's local time; pair with `timeZone`. |
| `timeZone` | Time zone for the schedule. |
| `preferredNumberOfHours` | Preferred shift length. |
| `projectId` | Ties the work to a project. |
| `locationName`, `address1`, `address2`, `city`, `state`, `postal`, `country` | Location. |
| `description` | Description. |
| `isActive` | Whether the opportunity is active. |
| `isLocalOnly` | Whether it is local only. |
| `preferredDateTime` | Preferred date/time. |
| `currentNeed` | How many volunteers are still needed. |
| `currentPriority` | How urgent the need is. |
| `customFields` | Array of custom field objects; list them with `GET /api/VolunteerOpportunity/CustomFields`. |

`POST /api/VolunteerOpportunity/Query` body: `groups` (array of condition objects), `sortBy` (string), `descending` (boolean). Discover fields with `GET /api/VolunteerOpportunity/QueryOptions`.

Nested collections:

- **Organizers** – staff or volunteers running the opportunity. Create with `contactIndividualId`.
- **Volunteers** – individuals signed up to serve. Create with `contactIndividualId`, then log time via Attendance.
- **Attendance** – logged shifts. Create/update body: `timeZone`, `hours`, `startDateTimeUtc`, `endDateTimeUtc` (note the shift times are UTC – coordinated universal time). Deleting an opportunity is blocked once it has organizers or volunteers; archive it instead.

## Related skills

- `crm-fundamentals.md` – authentication, the full two-factor flow, base URL, paging, and update semantics.
- `crm-webhooks.md` – webhook event types, signature verification, retries, idempotency, and local testing.
- `crm-api-contacts.md` – contact and individual endpoints (the records that global search, tasks, and reminders reference).
- `crm-api-giving.md` – gift and project endpoints (the records that gift and project webhook events fire on).
- `crm-api-campaigns-events.md` – campaign and event endpoints (the records that event webhooks fire on).

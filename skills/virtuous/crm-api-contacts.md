# Virtuous CRM+ API: Contacts endpoints
Based on Virtuous CRM+ OpenAPI spec (2026), retrieved 2026-08-31.

All endpoints share host `https://api.virtuoussoftware.com` and base path `/api`, and use Bearer token auth in the `Authorization` header (see `crm-fundamentals.md` for tokens, rate limits, and error shapes; one endpoint below is HMAC-only). A Contact is a household or organization, not a person: people live in its `contactIndividuals`, postal addresses in `contactAddresses`, and each email or phone in a `ContactMethod` on an individual (Contact → Individual → Method, with Address hanging off the Contact). This file is the endpoint reference for the Contacts domain; for the data model see `crm-concepts.md` and for end-to-end recipes see `crm-workflows.md`.

## How this domain is shaped

- **Read** a contact with `GET /api/Contact/{contactId}`; **find** one by email or external reference with `GET /api/Contact/Find`; **search** free-text with `POST /api/Contact/Search`; **filter** structured fields with `POST /api/Contact/Query`.
- **Create** directly with `POST /api/Contact` (no dedupe) or, preferred for integrations, dedupe-safe through `POST /api/Contact/Transaction` (one) or `POST /api/Contact/Batch` (many).
- **Update** with `PUT /api/Contact/{contactId}` (send the full model – see gotchas).
- Sub-resources (`ContactIndividual`, `ContactAddress`, `ContactMethod`, `ContactNote`, `ContactTag`, `Relationship`, ...) are managed through their own top-level endpoints, each taking the parent id in the body or path.
- Lookup lists (types, prefixes, query options, custom-field definitions) back the write endpoints; cache them rather than hardcoding values.

---

## Quick reference

Every operation in the Contacts domain (91 total), grouped by resource. Paths are relative to `https://api.virtuoussoftware.com`.

### Contact (28)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Contact` | Create a contact directly with its individuals, addresses, methods. No dedupe check. |
| GET | `/api/Contact/Activity` | Recent activity on contacts the authenticated user follows. Pages with skip/take. |
| PUT | `/api/Contact/Archive/{contactId}` | Archive a contact (retained, restorable). Body: `archiveReason`. |
| POST | `/api/Contact/Batch` | Submit a batch of contacts through the dedupe-checking import process. |
| GET | `/api/Contact/ByReference/{referenceId}` | Get a contact by external reference id, no source needed. **HMAC auth only.** |
| GET | `/api/Contact/ByTag/{tagId}` | List contacts carrying a tag. Params: filter, sortBy, descending, skip, take. |
| GET | `/api/Contact/CustomCollections` | List custom collections defined for the Contact object. |
| GET | `/api/Contact/CustomFields` | List enabled custom fields for the Contact object. |
| GET | `/api/Contact/Find` | Find one contact by email, or referenceSource+referenceId (reference wins if both sent). |
| GET | `/api/Contact/Following` | List contacts the authenticated user follows. Pages with skip/take. |
| GET | `/api/Contact/Prefixes` | List configured prefixes/titles (Mr., Mrs., Dr., ...). |
| POST | `/api/Contact/Proximity` | Find contacts within distanceInMiles of a lat/long. Body: latitude, longitude, distanceInMiles. |
| POST | `/api/Contact/Query` | Query contacts (abbreviated results) by filter groups. Pages with skip/take. |
| POST | `/api/Contact/Query/FullContact` | Same query, full contact details in the results. |
| GET | `/api/Contact/QueryOptions` | Fields, operators, and values valid in a contact query. |
| GET | `/api/Contact/Receipts` | Receipts issued to a contact by email. Params: email, skip, take. |
| GET | `/api/Contact/Receipts/{receiptId}` | Get one receipt with its gifts and recipient. |
| POST | `/api/Contact/Search` | Free-text / type-ahead search across names, emails, identifying details. Body: `search`. |
| PUT | `/api/Contact/ToggleFollow/{contactId}` | Follow or unfollow a contact for the authenticated user. |
| POST | `/api/Contact/Transaction` | Submit one contact through the dedupe-checking import process (flat shape). |
| GET | `/api/Contact/Types` | List configured contact types (Household, Organization, Foundation, ...). |
| PUT | `/api/Contact/Unarchive/{contactId}` | Restore an archived contact. |
| GET | `/api/Contact/{contactId}` | Get the full contact: individuals, primary address, giving summary, custom fields, related-record URLs. |
| PUT | `/api/Contact/{contactId}` | Update a contact. Send the full model (see gotchas). |
| DELETE | `/api/Contact/{contactId}/Collection/{customCollectionId}` | Remove a custom-collection instance from the contact. |
| POST | `/api/Contact/{contactId}/Collection/{customCollectionId}` | Add a custom-collection instance to the contact. Body: `fields`. |
| PUT | `/api/Contact/{contactId}/Collection/{customCollectionId}` | Replace a custom-collection instance's field values. Body: `fields`. |
| GET | `/api/Contact/{referenceSource}/{referenceId}` | Get a contact by external reference source + id (Bearer auth). |

### ContactIndividual (16)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/ContactIndividual` | Add an individual (spouse, staff member) to an existing contact. Body needs `contactId`. |
| GET | `/api/ContactIndividual/ByContact/{contactId}` | List every individual on a contact, with their methods and primary/secondary flags. |
| GET | `/api/ContactIndividual/CustomCollections` | List custom collections defined for the Individual object. |
| GET | `/api/ContactIndividual/CustomFields` | List enabled custom fields for the Individual object. |
| GET | `/api/ContactIndividual/Find` | Find an individual by email. Param: email. |
| POST | `/api/ContactIndividual/Query` | Query individuals by filter groups. Pages with skip/take. Max take 1,000. |
| GET | `/api/ContactIndividual/QueryOptions` | Fields, operators, values valid in an individual query. |
| DELETE | `/api/ContactIndividual/{contactIndividualId}` | Delete an individual and their methods. Contact unaffected. |
| GET | `/api/ContactIndividual/{contactIndividualId}` | Get one individual: methods, birth date, custom fields. |
| PUT | `/api/ContactIndividual/{contactIndividualId}` | Update an individual. Send the full model. |
| GET | `/api/ContactIndividual/{contactIndividualId}/Avatar` | Get the individual record including current avatarUrl. |
| POST | `/api/ContactIndividual/{contactIndividualId}/Avatar` | Upload an avatar photo (multipart form data). |
| DELETE | `/api/ContactIndividual/{contactIndividualId}/Collection/{customCollectionId}` | Remove a collection instance. Param: collectionInstanceId. |
| POST | `/api/ContactIndividual/{contactIndividualId}/Collection/{customCollectionId}` | Add a collection instance. Body: name, fields. |
| PUT | `/api/ContactIndividual/{contactIndividualId}/Collection/{customCollectionId}` | Replace a collection instance's field values. Body: fields. |
| GET | `/api/ContactIndividual/{contactIndividualId}/EmailList` | List email lists the individual belongs to. Pages with skip/take. |

### ContactAddress (7)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/ContactAddress` | Add an address to a contact. Body needs `contactId`; `setAsPrimary` for mailing address. |
| PUT | `/api/ContactAddress/Archive/{contactAddressId}` | Archive an address (kept for history, not used for mailings). |
| GET | `/api/ContactAddress/ByContact/{contactId}` | List a contact's addresses, with primary flag and seasonal dates. |
| PUT | `/api/ContactAddress/Unarchive/{contactAddressId}` | Restore an archived address (does not make it primary). |
| DELETE | `/api/ContactAddress/{contactAddressId}` | Delete an address. Archive instead to keep history. |
| GET | `/api/ContactAddress/{contactAddressId}` | Get one address. |
| PUT | `/api/ContactAddress/{contactAddressId}` | Update an address. Send the full model. |

### ContactMethod (8)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/ContactMethod` | Add a phone/email/other method to an individual. Body needs `contactIndividualId`, `type`, `value`. |
| PUT | `/api/ContactMethod/Archive/{contactMethodId}` | Archive a method (kept for history, not used for outreach). |
| GET | `/api/ContactMethod/RelatedTypes` | Method types related to one type. Param: name. |
| GET | `/api/ContactMethod/Types` | List configured method types (Home Email, Work Phone, Mobile Phone, ...). |
| PUT | `/api/ContactMethod/Unarchive/{contactMethodId}` | Restore an archived method (does not make it primary). |
| DELETE | `/api/ContactMethod/{contactMethodId}` | Delete a method. Archive instead to keep history. |
| GET | `/api/ContactMethod/{contactMethodId}` | Get one method: type, value, opt-in, primary flag. |
| PUT | `/api/ContactMethod/{contactMethodId}` | Update a method. Send the full model. |

### ContactNote (11)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/ContactNote` | Record a note on a contact. Body needs `contactId`; `type`, `note`, `important`, `timeSpent`. |
| GET | `/api/ContactNote/ByContact/{contactId}` | List notes on a contact. Params: sortBy, descending, skip, take. |
| GET | `/api/ContactNote/CustomFields` | List enabled custom fields for the Contact Note object. |
| POST | `/api/ContactNote/Email` | File an email exchange as note(s); matches from/to emails to individuals. Body: fromEmail, toEmail, subject, body. |
| GET | `/api/ContactNote/Important/ByContact/{contactId}` | List only important notes on a contact. Params: sortBy, descending, skip, take. |
| POST | `/api/ContactNote/Query` | Query notes by filter groups. Pages with skip/take. Max take 1,000. |
| GET | `/api/ContactNote/QueryOptions` | Query options for Contact Notes. |
| GET | `/api/ContactNote/Types` | List configured note types (Call, Email, Visit, ...). |
| DELETE | `/api/ContactNote/{noteId}` | Delete a note. Cannot be undone. |
| GET | `/api/ContactNote/{noteId}` | Get one note: type, body, any attached reminder. |
| PUT | `/api/ContactNote/{noteId}` | Update a note. Send the full model. |

### ContactTag (3)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/ContactTag` | Apply an existing tag to a contact. Body: `tagId`, `contactId`. |
| GET | `/api/ContactTag/ByContact/{contactId}` | List tags applied to a contact. Pages with skip/take. |
| DELETE | `/api/ContactTag/{contactTagId}` | Remove a tag from a contact. Use the `contactTagId`, not the `tagId`. |

### Tag (2)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/Tag` | List all tags in the org with per-tag contact counts. Pages with skip/take. |
| POST | `/api/Tag/Search` | Search tags by name (full or partial). Body: `search`. Pages with skip/take. |

### ContactReference (2)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/ContactReference` | Store a referenceSource+referenceId pair on a contact. Body: contactId, referenceSource, referenceId. |
| DELETE | `/api/ContactReference/{referenceSource}` | Remove a reference. Param: referenceId. Contact unaffected. |

### Relationship (5)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Relationship` | Record a relationship between two contacts or individuals; inverse recorded automatically. |
| GET | `/api/Relationship/ByContact/{contactId}` | List relationships on a contact (both sides). Pages with skip/take. |
| GET | `/api/Relationship/Types` | List configured relationship types, each with its inverse (Employer / Employee). |
| DELETE | `/api/Relationship/{relationshipId}` | Delete a relationship and its inverse. |
| PUT | `/api/Relationship/{relationshipId}` | Update a relationship. Body: relationshipType, notes. |

### OrganizationGroup (6)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/OrganizationGroup` | List org groups (departments, chapters, campuses). Params: filter, skip, take. |
| GET | `/api/OrganizationGroup/ByContact/{contactId}` | List groups a contact belongs to. |
| GET | `/api/OrganizationGroup/{organizationGroupId}` | Get one group: name, location, description. |
| GET | `/api/OrganizationGroup/{organizationGroupId}/contacts` | List contacts in a group. Pages with skip/take. |
| DELETE | `/api/OrganizationGroup/{organizationGroupId}/contacts/{contactId}` | Remove a contact from a group. |
| PUT | `/api/OrganizationGroup/{organizationGroupId}/contacts/{contactId}` | Add a contact to a group. Empty body; both ids in the path. |

### Tribute (3)

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/Tribute` | Create a tribute (honoree of an in-honor/in-memory gift). |
| GET | `/api/Tribute/Search` | Find a tribute. Params: firstName, lastName, city, state, tributeType. |
| PUT | `/api/Tribute/{tributeId}` | Update a tribute. Send the full model. |

---

## Deep dives

### Create a contact: direct vs dedupe-safe import

Two shapes create a contact, and choosing between them is the most consequential decision in a write integration.

**`POST /api/Contact` – direct, nested, no dedupe.** You build the whole hierarchy in one nested body. It applies immediately and does **not** check for duplicates, so only use it when you already know the contact does not exist (for example, right after `GET /api/Contact/Find` returns nothing).

Body fields (from the spec):

| Field | Type | Notes |
| --- | --- | --- |
| `contactType` | string | e.g. `Household`, `Organization`. Fetch valid values from `GET /api/Contact/Types`. |
| `name` | string | Display name of the household/org, e.g. `"Wayne, Bruce"`. |
| `informalName`, `description`, `website` | string | Optional descriptive fields. |
| `maritalStatus` | string | |
| `anniversaryMonth` / `anniversaryDay` / `anniversaryYear` | string | Household anniversary parts. |
| `referenceSource` / `referenceId` | string | External-system reference set at creation. |
| `originSegmentId` | string | Origin segment. |
| `isPrivate` / `isArchived` | string (boolean) | Lifecycle flags. |
| `contactAddresses` | array<object> | Addresses on the contact (see ContactAddress fields). |
| `contactIndividuals` | array<object> | People on the contact (see ContactIndividual fields). |
| `customFields` | string | Custom field values. |
| `customCollections` | array<object> | Custom collection instances. |

A nested individual donor body (household with one primary individual, one email, one phone, one address):

```json
{
  "contactType": "Household",
  "name": "Wayne, Bruce",
  "contactIndividuals": [
    {
      "firstName": "Bruce",
      "lastName": "Wayne",
      "isPrimary": true,
      "contactMethods": [
        { "type": "Home Email",   "value": "bruce@wayne.example", "isPrimary": true, "isOptedIn": true },
        { "type": "Mobile Phone", "value": "555-0100",            "isPrimary": true }
      ]
    }
  ],
  "contactAddresses": [
    {
      "address1": "1007 Mountain Drive",
      "city": "Gotham",
      "state": "NJ",
      "postal": "07001",
      "country": "US",
      "setAsPrimary": true
    }
  ]
}
```

Note the field placement: `firstName`/`lastName` sit on the **individual**, not the contact; the email string sits on a **contact method**, not the individual. This is the hierarchy that trips up most integrations.

> Success is `200 OK`, not `201 Created`. The new contact's id is in the response body. Treat any success from this endpoint as a creation regardless of status code.

**`POST /api/Contact/Transaction` – dedupe-safe, flat, async (recommended).** This submits one contact through the import process, which checks it for changes and duplicates before applying it (matching on email, phone, address, name, and references, then creating only if nothing matches, otherwise merging). The body is **flat** – the individual and method fields are denormalized to the top level rather than nested:

| Field | Notes |
| --- | --- |
| `referenceSource`, `referenceId` | External reference used for matching. |
| `contactType`, `name` | Contact-level. |
| `title`, `firstName`, `middleName`, `lastName`, `suffix` | Primary individual, flattened. |
| `emailType`, `email` | One email, flattened (type + value). |
| `phoneType`, `phone` | One phone, flattened. |
| `address1`, `address2`, `city`, `state`, `postal`, `country` | One address, flattened. |
| `eventId`, `eventName`, `invited`, `rsvp`, `rsvpResponse`, `attended` | Optional event attendance to attach. |
| `tags` | Tags to apply. |
| `originSegmentCode` | Origin segment (by code, vs `originSegmentId` on `POST /api/Contact`). |
| `emailLists` | array<string> – email lists to subscribe. |
| `customFields` | Custom field values. |
| `volunteerAttendances` | array<object> – volunteer attendance to attach. |

```json
{
  "referenceSource": "Stripe",
  "referenceId": "cus_abc123",
  "contactType": "Household",
  "name": "Wayne, Bruce",
  "firstName": "Bruce",
  "lastName": "Wayne",
  "emailType": "Home Email",
  "email": "bruce@wayne.example",
  "phoneType": "Mobile Phone",
  "phone": "555-0100",
  "address1": "1007 Mountain Drive",
  "city": "Gotham",
  "state": "NJ",
  "postal": "07001",
  "country": "US"
}
```

Because it runs through import matching, this is the path to prefer for partner integrations. See `crm-workflows.md` for the transaction lifecycle.

**`POST /api/Contact/Batch` – dedupe-safe, many at once.** Same import-and-match process for a batch. Body: `referenceSource` (string) and `contacts` (array<object>, each contact like a Transaction entry). Use it for bulk backfills.

### Find or search before you create

`POST /api/Contact` has no duplicate protection, so a synchronous create should always look first.

- **`GET /api/Contact/Find`** – narrow, exact lookup. Send `email`, or `referenceSource` + `referenceId`; if you send both, the reference pair wins. Returns a single matched contact.

  ```
  GET /api/Contact/Find?email=bruce%40wayne.example
  GET /api/Contact/Find?referenceSource=Stripe&referenceId=cus_abc123
  ```

- **`POST /api/Contact/Search`** – broad free-text, good for type-ahead. Body `{ "search": "wayne" }`, paged with `skip`/`take`. Covers names, emails, and other identifying details. Use `POST /api/Contact/Query` instead when you need structured field filters.

Recommended synchronous upsert: `Find` by email/reference → if empty, `Query` by name + postal for fuzzy matches → create only if both are empty.

### Get a contact and its sub-resources

`GET /api/Contact/{contactId}` returns the full record: its individuals, primary address, giving summary, custom fields, and URLs to related records (gifts, recurring gifts, planned gifts). Illustrative response shape:

```json
{
  "id": 4821,
  "contactType": "Household",
  "name": "Wayne, Bruce",
  "contactIndividuals": [
    {
      "id": 9012,
      "firstName": "Bruce",
      "lastName": "Wayne",
      "isPrimary": true,
      "contactMethods": [
        { "id": 31001, "type": "Home Email",   "value": "bruce@wayne.example", "isPrimary": true },
        { "id": 31002, "type": "Mobile Phone", "value": "555-0100",            "isPrimary": true }
      ]
    }
  ],
  "address": {
    "id": 51001,
    "address1": "1007 Mountain Drive",
    "city": "Gotham", "state": "NJ", "postal": "07001", "country": "US",
    "isPrimary": true
  }
}
```

The response exposes the primary address as a single `address` object, while addresses are created and managed as a `contactAddresses` array / the `ContactAddress` resource. To enumerate sub-resources without pulling the whole contact, use the `ByContact` list endpoints: `GET /api/ContactIndividual/ByContact/{contactId}`, `GET /api/ContactAddress/ByContact/{contactId}`, `GET /api/ContactNote/ByContact/{contactId}`, `GET /api/ContactTag/ByContact/{contactId}`, `GET /api/Relationship/ByContact/{contactId}`, `GET /api/OrganizationGroup/ByContact/{contactId}`.

### Look a contact up by external reference id

Two endpoints resolve a contact from an external system's id, and they differ in what you must supply and how you authenticate:

| Endpoint | Auth | You must know | Use when |
| --- | --- | --- | --- |
| `GET /api/Contact/{referenceSource}/{referenceId}` | Bearer | Both source and id | Standard token integrations that know which source set the reference. |
| `GET /api/Contact/ByReference/{referenceId}` | **HMAC only** | Only the id | You have the external id but not the source. Requires HMAC credentials from Virtuous support. |

References are set at create/import time, or later with `POST /api/ContactReference` (`{ contactId, referenceSource, referenceId }`), and removed with `DELETE /api/ContactReference/{referenceSource}?referenceId=...`. Storing a reference lets you look the contact up by your own id instead of persisting the Virtuous id in your database.

### Query contacts with filters and paging

`POST /api/Contact/Query` returns matching contacts in **abbreviated** form; `POST /api/Contact/Query/FullContact` returns the same matches with **full** details (heavier payload). Both take the same body and page with `skip`/`take` query params.

Body fields (from the spec):

| Field | Type | Notes |
| --- | --- | --- |
| `groups` | array<object> | Filter groups; groups OR together, conditions within a group AND together. |
| `queryLocation` | object | Scopes the query. |
| `sortBy` | string | Sort field. |
| `descending` | string (boolean) | Sort direction. |
| `includeArchived` | string (boolean) | Defaults to excluding archived contacts; set true to include them. |

The exact field names, operators, and values that go inside `groups` come from **`GET /api/Contact/QueryOptions`** – call it first and build conditions from what it returns rather than guessing. The spec types `groups` only as `array<object>`; the standard Virtuous condition grammar looks like this (field/operator/value names are illustrative – take the real ones from QueryOptions):

```
POST /api/Contact/Query?skip=0&take=100
```
```json
{
  "groups": [
    {
      "conditions": [
        { "parameter": "Last Modified Date", "operator": "After", "value": "2026-08-01" }
      ]
    }
  ],
  "sortBy": "Last Name",
  "descending": "false",
  "includeArchived": "false"
}
```

Incremental sync anchors on the modified timestamp: query for contacts modified after your last run, page through with `skip`/`take`, and persist the newest `modifiedDateTimeUtc` you saw. Do **not** poll queries for brand-new or updated records on a tight loop – use a webhook for change notifications (per the spec's own guidance on the note query). Sibling query endpoints follow the same body shape: `POST /api/ContactIndividual/Query` and `POST /api/ContactNote/Query`, each with their own `QueryOptions` and a documented **max `take` of 1,000**.

Other filtered lists: `GET /api/Contact/ByTag/{tagId}` (params filter, sortBy, descending, skip, take) and `POST /api/Contact/Proximity` (`{ latitude, longitude, distanceInMiles }`, paged) for donors near a point.

### Update a contact

`PUT /api/Contact/{contactId}` updates a contact. Body fields:

| Field | Type |
| --- | --- |
| `contactType`, `name`, `informalName`, `description`, `website` | string |
| `maritalStatus`, `anniversaryMonth`, `anniversaryDay`, `anniversaryYear` | string |
| `originSegmentId`, `isPrivate` | string |
| `customFields` | array<object> |
| `customCollections` | array<object> |

The spec's own description says "excluding a property will remove its value from the object" and "the entire model is still required" – that is full-replacement PUT semantics. In practice the live API currently behaves like PATCH (omitted fields are not cleared), but that behavior is undocumented and could change. The safe, version-proof pattern is:

1. `GET /api/Contact/{contactId}` to read the current record.
2. Change only the fields you mean to change.
3. `PUT /api/Contact/{contactId}` with the complete model.

Every `PUT` in this domain (`ContactIndividual`, `ContactAddress`, `ContactMethod`, `ContactNote`, `Relationship`, `Tribute`) carries the same "full model required" note – apply the read-modify-write pattern to all of them.

### Add and update individuals

`POST /api/ContactIndividual` adds a person to an existing contact. Body:

| Field | Notes |
| --- | --- |
| `contactId` | **Required** – the contact they belong to. |
| `firstName`, `lastName`, `prefix`, `middleName`, `suffix` | Name parts. |
| `gender`, `passion`, `avatarUrl` | |
| `setAsPrimary` / `setAsSecondary` | Place them as the household's primary or secondary. |
| `birthMonth`, `birthDay`, `birthYear`, `approximateAge` | Birth date parts. |
| `isDeceased`, `deceasedDate` | |
| `contactMethods` | array<object> – methods to create with the individual. |
| `customFields`, `customCollections` | array<object> |

```json
{
  "contactId": 4821,
  "firstName": "Selina",
  "lastName": "Kyle",
  "setAsSecondary": true,
  "contactMethods": [
    { "type": "Home Email", "value": "selina@wayne.example", "setAsPrimary": true }
  ]
}
```

`PUT /api/ContactIndividual/{contactIndividualId}` updates one; it takes the same fields minus `contactId` and `contactMethods` (manage methods through the `ContactMethod` endpoints). `DELETE /api/ContactIndividual/{contactIndividualId}` removes the person and their methods but leaves the contact. Avatars: `GET`/`POST /api/ContactIndividual/{contactIndividualId}/Avatar` (upload as multipart form data).

> Write payloads use `setAsPrimary` / `setAsSecondary`; read payloads report `isPrimary` / `isSecondary`. Send the `setAs...` form when creating or updating.

### Add and update contact methods (email/phone)

A `ContactMethod` belongs to an **individual**, not the contact. `POST /api/ContactMethod`:

| Field | Notes |
| --- | --- |
| `contactIndividualId` | **Required** – the individual it belongs to. |
| `type` | e.g. `Home Email`, `Mobile Phone`. Values from `GET /api/ContactMethod/Types`. |
| `value` | The email address or phone number. |
| `isOptedIn` | Consent flag. |
| `setAsPrimary` | Make it the individual's primary method of that kind. |

```json
{ "contactIndividualId": 9012, "type": "Work Email", "value": "bruce@wayne-ent.example", "setAsPrimary": false, "isOptedIn": true }
```

`PUT /api/ContactMethod/{contactMethodId}` updates one (`type`, `value`, `isOptedIn`, `setAsPrimary`). To retire a method keep history with `PUT /api/ContactMethod/Archive/{contactMethodId}` rather than `DELETE`. `GET /api/ContactMethod/Types` and `GET /api/ContactMethod/RelatedTypes?name=...` back the `type` field.

### Add and update addresses

A `ContactAddress` belongs to the **contact**. `POST /api/ContactAddress`:

| Field | Notes |
| --- | --- |
| `contactId` | **Required.** |
| `label` | Display label ("Home", "Work", "Seasonal"). |
| `address1`, `address2`, `city`, `state`, `postal`, `country` | Postal parts. |
| `setAsPrimary` | Make it the mailing address. |
| `startMonth`, `startDay`, `endMonth`, `endDay` | Seasonal date range (snowbird addresses). |

`PUT /api/ContactAddress/{contactAddressId}` updates one (same fields minus `contactId`). Retire with `PUT /api/ContactAddress/Archive/{contactAddressId}` to keep history, or `DELETE` to remove.

### Tags

Tag definitions are created in the CRM, not the API; the API applies existing tags. To apply one you need its `tagId`:

1. `GET /api/Tag` (all tags with counts) or `POST /api/Tag/Search` (`{ "search": "major" }`) to find the `tagId`.
2. `POST /api/ContactTag` with `{ "tagId": 55, "contactId": 4821 }` to apply it.
3. `GET /api/ContactTag/ByContact/{contactId}` to list a contact's tags.
4. `DELETE /api/ContactTag/{contactTagId}` to remove one – pass the **`contactTagId`** from the contact's tag list, not the `tagId`.

### Notes

`POST /api/ContactNote` records an interaction on a contact:

| Field | Notes |
| --- | --- |
| `contactId` | **Required.** |
| `type` | Note type; values from `GET /api/ContactNote/Types` (Call, Email, Visit, ...). |
| `note` | The body text. |
| `noteDateTime` | When it happened. |
| `important` | Surface it on the contact record. |
| `private` | Restrict visibility. |
| `timeSpent` | Duration of the interaction. |

List with `GET /api/ContactNote/ByContact/{contactId}` (or `/Important/ByContact/{contactId}` for flagged ones), update with `PUT /api/ContactNote/{noteId}`, delete with `DELETE /api/ContactNote/{noteId}` (permanent). `POST /api/ContactNote/Email` files an email as note(s): it matches `fromEmail`/`toEmail` to individuals and can create more than one note (one per matched contact), so expect an array in the response.

### Relationships

`POST /api/Relationship` records a link between two contacts, or between specific individuals on them, and writes the inverse on the other side automatically:

| Field | Notes |
| --- | --- |
| `contactId` | One side (contact). |
| `contactIndividualId` | Optional – a specific individual on that side. |
| `relatedContactId` | The other side (contact). |
| `relatedContactIndividualId` | Optional – a specific individual on the other side. |
| `relationshipType` | Type; values from `GET /api/Relationship/Types` (each has an inverse, e.g. Employer / Employee). |
| `notes` | Free text. |

List with `GET /api/Relationship/ByContact/{contactId}`, update with `PUT /api/Relationship/{relationshipId}` (`relationshipType`, `notes`), delete with `DELETE /api/Relationship/{relationshipId}` (also removes the inverse).

### Organization groups, tributes, custom collections

- **Organization groups** are departments/chapters/campuses. Membership is managed by path only: `PUT /api/OrganizationGroup/{organizationGroupId}/contacts/{contactId}` adds (empty body), `DELETE` the same path removes. List members with `.../contacts` (paged).
- **Tributes** name the honoree of an in-honor/in-memory gift. `POST /api/Tribute` (`tributeType`, name, address parts, `contactIndividualId`, `defaultAcknowledgeeIndividualId`), find with `GET /api/Tribute/Search`, update with `PUT /api/Tribute/{tributeId}`. Referenced from gift records – see `crm-api-giving.md`.
- **Custom collections** attach repeatable structured records. The instance lifecycle is create → returns a `collectionInstanceId` → update replaces field values (send the full set; omitted fields are cleared) → delete. Contact-level: `POST`/`PUT`/`DELETE /api/Contact/{contactId}/Collection/{customCollectionId}`. Individual-level: the same under `/api/ContactIndividual/{contactIndividualId}/Collection/{customCollectionId}`; its `DELETE` takes the instance as a `collectionInstanceId` query param, and its `POST` accepts a `name` alongside `fields`. Discover collection definitions with `GET /api/Contact/CustomCollections` and `GET /api/ContactIndividual/CustomCollections`.

---

## Gotchas

- **Field placement follows the hierarchy.** `firstName`/`lastName`/birth date/gender live on `ContactIndividual`, not `Contact`. Email and phone live on `ContactMethod` (attached to an individual), never as a top-level string on the contact or individual. Household-level fields (name, marital status, anniversary) live on `Contact`.
- **Direct create does not dedupe.** `POST /api/Contact` always makes a new record. For dedupe, use `POST /api/Contact/Transaction` (one), `POST /api/Contact/Batch` (many), or find-then-create with `GET /api/Contact/Find` + `POST /api/Contact/Query`.
- **The Transaction body is flat, the Contact body is nested.** Transaction/Batch denormalize the primary individual, one email, one phone, and one address to top-level keys (`firstName`, `email`, `phone`, `address1`, ...); `POST /api/Contact` nests them under `contactIndividuals` / `contactMethods` / `contactAddresses`. Do not mix the two shapes.
- **`POST /api/Contact` returns `200`, not `201`.** The new id is in the body. Any success means the record was created.
- **`PUT` claims full-replacement.** The spec says omitting a field clears it and "the entire model is still required," though the live API currently behaves like PATCH. Do not rely on the undocumented PATCH behavior: `GET`, modify, then `PUT` the complete model.
- **Write vs read primary flags.** Send `setAsPrimary` / `setAsSecondary` on writes; you read back `isPrimary` / `isSecondary`.
- **Reference lookups differ by auth.** `GET /api/Contact/{referenceSource}/{referenceId}` is Bearer and needs both parts; `GET /api/Contact/ByReference/{referenceId}` needs only the id but is **HMAC-only** and requires credentials from Virtuous support.
- **Archive vs delete.** Archiving (contacts, addresses, methods) retains the record and its history and is reversible with the matching Unarchive endpoint; delete is permanent. Prefer archive to preserve giving history. Note contacts have Archive/Unarchive but note deletion (`DELETE /api/ContactNote/{noteId}`) cannot be undone.
- **`includeArchived` defaults off.** Contact queries exclude archived records unless you set `includeArchived: true`.
- **Paging and query limits.** Page every list/query with `skip`/`take`. `POST /api/ContactIndividual/Query` and `POST /api/ContactNote/Query` document a **max `take` of 1,000`**; splitting large pulls avoids timeouts. Don't poll queries for new/changed records – use webhooks.
- **Tag removal uses `contactTagId`.** `DELETE /api/ContactTag/{contactTagId}` takes the join id from the contact's tag list, not the underlying `tagId`.
- **Configurable enums.** `contactType`, method types, note types, relationship types, and prefixes are org-configured. Fetch them from their list endpoints (`/Types`, `/Prefixes`, `/QueryOptions`) and cache – do not hardcode the strings.
- **Custom collection deletes are inconsistent.** Contact-level delete identifies the instance by the `{customCollectionId}` path segment; individual-level delete needs a `collectionInstanceId` query param. Keep the `collectionInstanceId` returned at create time.

---

## Related skills

- `crm-concepts.md` – the Contact data model, hierarchy, lifecycle, and matching concepts behind these endpoints.
- `crm-workflows.md` – end-to-end recipes: create a contact, update a contact, query by filters, the transaction/import lifecycle.
- `crm-fundamentals.md` – base URL, Bearer and HMAC authentication, headers, paging, rate limits, and error handling.
- `crm-api-giving.md` – gifts, pledges, recurring gifts, and receipts that reference a contact (and tributes).
- `crm-api-campaigns-events.md` – campaigns, segments, and the events/RSVP data the Transaction endpoint can attach.
- `crm-api-system.md` – custom fields and collections definitions, webhooks for change notifications, and other org-level configuration.

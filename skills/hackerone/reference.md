# HackerOne API: Object Reference

Based on HackerOne API v1 documentation. All objects follow JSON:API format with `id`, `type`, `attributes`, and `relationships`.

## Report

The core resource — a vulnerability submission.

| Attribute | Type | Description |
|-----------|------|-------------|
| `title` | string | Report title |
| `vulnerability_information` | string | Detailed description (not Markdown-parsed by API) |
| `state` | string | Current state (see below) |
| `created_at` | ISO 8601 | Submission time |
| `triaged_at` | ISO 8601 | When triaged |
| `closed_at` | ISO 8601 | When closed |
| `disclosed_at` | ISO 8601 | When disclosed |
| `bounty_awarded_at` | ISO 8601 | When bounty awarded |
| `swag_awarded_at` | ISO 8601 | When swag awarded |
| `last_reporter_activity_at` | ISO 8601 | Last reporter action |
| `first_program_activity_at` | ISO 8601 | First program response |
| `last_program_activity_at` | ISO 8601 | Last program action |
| `last_activity_at` | ISO 8601 | Any last action |
| `last_public_activity_at` | ISO 8601 | Last public action |
| `reporter_agreed_on_going_public_at` | ISO 8601 | Reporter agreed to disclose |
| `cve_ids` | array | Associated CVE identifiers |
| `source` | string | Origin (for imported reports) |

**Report states:** `new`, `pending-program-review`, `triaged`, `needs-more-info`, `resolved`, `not-applicable`, `informative`, `duplicate`, `spam`, `retesting`

**Relationships:** `reporter`, `program`, `severity`, `swag`, `attachments`, `weakness`, `activities`, `bounties`, `summaries`, `structured_scope`

## User

| Attribute | Type | Description |
|-----------|------|-------------|
| `username` | string | Unique handle |
| `name` | string | Display name |
| `disabled` | boolean | Account status |
| `created_at` | ISO 8601 | Registration date |
| `profile_picture` | object | URLs at 62x62, 82x82, 110x110, 260x260 |
| `bio` | string | Optional |
| `website` | string | Optional |
| `location` | string | Optional |
| `reputation` | integer | Hacker reputation score |
| `signal` | number | Signal score |
| `impact` | number | Impact score |
| `hackerone_triager` | boolean | HackerOne triager status |

**Relationships:** `participating_programs`

## Program

| Attribute | Type | Description |
|-----------|------|-------------|
| `handle` | string | Unique identifier |
| `name` | string | Display name |
| `currency` | string | Bounty currency |
| `policy` | string | Disclosure policy text |
| `profile_picture` | string | URL |
| `submission_state` | string | Accepting submissions? |
| `triage_active` | boolean | Triage enabled |
| `state` | string | Program state |
| `started_accepting_at` | ISO 8601 | Launch date |
| `offers_bounties` | boolean | Paid program |
| `open_scope` | boolean | Open scope policy |
| `fast_payments` | boolean | Fast payment enabled |
| `gold_standard_safe_harbor` | boolean | Safe harbor policy |
| `allows_bounty_splitting` | boolean | Split bounties allowed |

**Hacker-specific fields** (in hacker API context):
`number_of_reports_for_user`, `number_of_valid_reports_for_user`, `bounty_earned_for_user`, `last_invitation_accepted_at_for_user`, `bookmarked`

**Relationships:** `structured_scopes`

## Severity

CVSS-based severity assessment.

| Attribute | Type | Values |
|-----------|------|--------|
| `rating` | string | `none`, `low`, `medium`, `high`, `critical` |
| `score` | number | CVSS score |
| `author_type` | string | `User`, `Team` |
| `user_id` | string | Author ID |
| `attack_vector` | string | `network`, `adjacent`, `local`, `physical` |
| `attack_complexity` | string | `low`, `high` |
| `privileges_required` | string | `none`, `low`, `high` |
| `user_interaction` | string | `none`, `required` |
| `scope` | string | `unchanged`, `changed` |
| `confidentiality` | string | `none`, `low`, `high` |
| `integrity` | string | `none`, `low`, `high` |
| `availability` | string | `none`, `low`, `high` |

## Structured Scope

Program-defined asset boundaries.

| Attribute | Type | Description |
|-----------|------|-------------|
| `asset_identifier` | string | Target (URL, domain, app ID, etc.) |
| `asset_type` | string | Classification |
| `eligible_for_bounty` | boolean | Pays bounties |
| `eligible_for_submission` | boolean | Accepts reports |
| `max_severity` | string | `none`/`low`/`medium`/`high`/`critical` |
| `confidentiality_requirement` | string | `none`/`low`/`medium`/`high` |
| `integrity_requirement` | string | `none`/`low`/`medium`/`high` |
| `availability_requirement` | string | `none`/`low`/`medium`/`high` |
| `instruction` | string | Eligibility notes |
| `reference` | string | External reference |
| `created_at` / `updated_at` | ISO 8601 | Timestamps |

## Activity (Base)

| Attribute | Type | Description |
|-----------|------|-------------|
| `report_id` | string | Associated report |
| `message` | string/null | Comment content (not Markdown-parsed) |
| `internal` | boolean | `true` = visible only to program staff |
| `created_at` / `updated_at` | ISO 8601 | Timestamps |

**Relationships:** `actor` (user or program), `attachments`

See [customer-extras.md](./customer-extras.md) for all 50+ activity subtypes.

## Bounty

| Attribute | Type | Description |
|-----------|------|-------------|
| `amount` | string | Bounty amount |
| `bonus_amount` | string | Bonus amount |
| `awarded_amount` | string | Awarded amount |
| `awarded_bonus_amount` | string | Awarded bonus |
| `awarded_currency` | string | Currency code |
| `created_at` | ISO 8601 | Award date |

## Attachment

| Attribute | Type | Description |
|-----------|------|-------------|
| `file_name` | string | Original filename |
| `content_type` | string | MIME type |
| `file_size` | integer | Size in bytes |
| `expiring_url` | string | Temporary URL (**expires after 60 minutes**) |
| `created_at` | ISO 8601 | Upload time |

## Weakness

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | string | Weakness name |
| `description` | string | Description |
| `external_id` | string | CWE/CAPEC reference |
| `created_at` | ISO 8601 | Creation date |

## Group

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | string | Group name |
| `created_at` | ISO 8601 | Creation date |
| `permissions` | array | `reward_management`, `program_management`, `user_management`, `report_management` |

## Earning

| Attribute | Type | Description |
|-----------|------|-------------|
| `amount` | string | Earning amount |
| `created_at` | ISO 8601 | Date |

**Type values:** `earning-bounty-earned`, `earning-retest-completed`, `earning-pentest-completed`

**Relationships:** `team`, `bounty`, `pentester`, `report_retest_user`

## Payout

| Attribute | Type | Description |
|-----------|------|-------------|
| `amount` | string | Payout amount |
| `paid_out_at` | ISO 8601 | Date |
| `reference` | string | Transaction reference |
| `payout_provider` | string | e.g., PayPal |
| `status` | string | Payment status |

## Hacktivity Item

Limited report info for public feeds.

| Attribute | Type | Description |
|-----------|------|-------------|
| `title` | string | Report title |
| `substate` | string | Report substate |
| `url` | string | Report URL |
| `disclosed_at` | ISO 8601 | Disclosure date |
| `submitted_at` | ISO 8601 | Submission date |
| `disclosed` | boolean | Is publicly disclosed |
| `cve_ids` | array | CVE identifiers |
| `cwe` | string | CWE classification |
| `severity_rating` | string | Severity level |
| `votes` | integer | Vote count |
| `total_awarded_amount` | string | Total bounty |

**Relationships:** `report_generated_content`, `reporter`, `program`

## Report Intent

| Attribute | Type | Description |
|-----------|------|-------------|
| `title` | string | Draft title |
| `description` | string | Vulnerability details |
| `state` | string | `pending`, `ready_to_submit`, `submitted` |
| `has_failing_jobs` | boolean | AI job failures |
| `has_canceled_jobs` | boolean | AI job cancellations |
| `job_status_by_type` | object | Status per AI job type |
| `metadata` | object | Analysis results |

**Relationships:** `program`, `report`, `attachments`

## Report Summary

| Attribute | Type | Description |
|-----------|------|-------------|
| `content` | string | Summary text |
| `category` | string | `researcher`, `team`, `triage` |
| `created_at` / `updated_at` | ISO 8601 | Timestamps |

**Relationships:** `user`

## Other Types

| Type | Description |
|------|-------------|
| `program_small` | Minimal program (handle only) |
| `report-retest` | Retest record, relationship to report |
| `report-retest-user` | Retest completion, `completed_at` attribute |
| `pentest` | Pentest engagement (`name`, `description`) |
| `pentester` | Pentest completion (`completed_at`, `award_amount`) |
| `report_generated_content` | AI-generated summary (`hacktivity_summary`) |
| `swag` | Non-monetary reward (`sent` boolean) |
| `address` | Postal info for swag (name, street, city, postal_code, state, country, tshirt_size, phone_number) |
| `custom_field_attribute` | Custom field definition (`label`, `configuration`, `archived_at`) |

**T-shirt sizes:** `M_Small`, `M_Medium`, `M_Large`, `M_XLarge`, `M_XXLarge`, `W_Small`, `W_Medium`, `W_Large`, `W_XLarge`, `W_XXLarge`

<!--
SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

# Address status codes

DAWA and Adressevælgeren use different numbers for the same address states.
DAWA had its own simplified scale, while Adressevælgeren uses the official codes
from Danmarks Adresseregister (DAR).

## DAWA

DAWA's `status` field used its own scale:

| Code | Meaning                  |
|------|--------------------------|
| 1    | Gældende (current)       |
| 2    | Nedlagt (retired)        |
| 3    | Foreløbig (provisional)  |
| 4    | Henlagt (shelved)        |

In practice DAWA only served 1 and 3, as addresses with status 2 or 4 were not
included. DAWA also had a `darstatus` field, which passed through the DAR code
(2 to 5, see below).

## Adressevælgeren (DAR)

Adressevælgeren's `status` field is the DAR code itself, see
[DAR's livscyklus code list](https://danmarksadresser.dk/adressedata/kodelister/livscyklus).

Addresses, husnumre and named roads:

| Code | Name                | Meaning                                                    |
|------|---------------------|------------------------------------------------------------|
| 1    | Intern forberedelse | Internal draft in the municipality, never published        |
| 2    | Foreløbig           | Provisional, published before it becomes current           |
| 3    | Gældende            | Current                                                    |
| 4    | Nedlagt             | Retired, after having been current                         |
| 5    | Henlagt             | Shelved, after only ever having been provisional           |
| 6    | Slettet             | Deleted                                                    |

Access points (`adgangspunkt`) use their own codes:

| Code | Name        | Meaning                                      |
|------|-------------|----------------------------------------------|
| 6    | Slettet     | Deleted, after having been not in use        |
| 7    | Ikke i brug | Not in use, no addresses attached            |
| 8    | I brug      | In use                                       |
| 9    | Udgået      | Retired, after having been in use            |

Lookups return the status as a string (`"3"`), while `/vask/` returns an
integer (`3`).

## Mapping in the DAR client

The DAR client returns replies in DAWA's `struktur=mini` shape, so it maps the
DAR code to DAWA's `status` and keeps the DAR code as `darstatus`. The mapping
is the same as DAWA's own (its `dar1_status_til_dawa_status` SQL function):

| DAR code (`darstatus`) | DAWA code (`status`) | Meaning   |
|------------------------|----------------------|-----------|
| 2                      | 3                    | Foreløbig |
| 3                      | 1                    | Gældende  |
| 4                      | 2                    | Nedlagt   |
| 5                      | 4                    | Henlagt   |

DAR codes 1 and 6 have no DAWA equivalent and are mapped to `status: None`.
They should not appear in practice, as they are never published.

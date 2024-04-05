<!--
SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

# RA Utils

RA Utils is a collection of utilities used by [OS2mo](https://github.com/OS2mo/os2mo) and friends.

## Usage
Usage depends on the utility used, but as an example `apply` can be used as:

```Python
from ra_utils.apply import apply

@apply
def dual(key, value):
    return value

print(dual(('k', 'v')))  # --> 'v'
```

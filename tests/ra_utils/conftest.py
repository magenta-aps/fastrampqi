# SPDX-FileCopyrightText: 2021 Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import os

from hypothesis import settings

settings.register_profile("ci", max_examples=100, deadline=None)
settings.register_profile("deep", max_examples=10000, deadline=None)
settings.register_profile("dev", max_examples=100, deadline=None)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))

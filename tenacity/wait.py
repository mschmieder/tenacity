# Copyright 2016 Julien Danjou
# Copyright 2016 Joshua Harlow
# Copyright 2013-2014 Ray Holder
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random

from tenacity import _utils


class wait_jitter(object):
    """Wait strategy that waits a random amount of time (bounded by a max)."""

    def __init__(self, max):
        self.max = max

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        return random.random() * self.max


class wait_fixed(object):
    """Wait strategy that waits a fixed amount of time between each retry."""

    def __init__(self, wait):
        self.wait_fixed = wait

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        return self.wait_fixed


class wait_none(wait_fixed):
    """Wait strategy that doesn't wait at all before retrying."""

    def __init__(self):
        super(wait_none, self).__init__(0)


class wait_random(object):
    """Wait strategy that waits a random amount of time between min/max."""

    def __init__(self, min=0, max=1):
        self.wait_random_min = min
        self.wait_random_max = max

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        return random.randint(self.wait_random_min, self.wait_random_max)


class wait_combine(object):
    """Combine several waiting strategies."""

    def __init__(self, *strategies):
        self.wait_funcs = strategies

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        return sum(map(
            lambda x: x(previous_attempt_number, delay_since_first_attempt),
            self.wait_funcs))


class wait_chain(object):
    """Chain two or more waiting strategies.

    If all strategies are exhausted, the very last strategy is used
    thereafter.

    For example::

        @retry(wait=wait_chain(*[wait_fixed(1) for i in range(3)] +
                               [wait_fixed(2) for j in range(5)] +
                               [wait_fixed(5) for k in range(4)))
        def wait_chained():
            print("Wait 1s for 3 attempts, 2s for 5 attempts and 5s
                   thereafter.")
    """

    def __init__(self, *strategies):
        self.strategies = list(strategies)

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        wait_func = self.strategies[0]
        if len(self.strategies) > 1:
            self.strategies.pop(0)
        return wait_func(previous_attempt_number, delay_since_first_attempt)


class wait_incrementing(object):
    """Wait an incremental amount of time after each attempt.

    Starting at a starting value and incrementing by a value for each attempt
    (and restricting the upper limit to some maximum value).
    """

    def __init__(self, start=0, increment=100, max=_utils.MAX_WAIT):
        self.start = start
        self.increment = increment
        self.max = max

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        result = self.start + (
            self.increment * (previous_attempt_number - 1)
        )
        return max(0, min(result, self.max))


class wait_exponential(object):
    """Wait strategy that applies exponential backoff.

    It allows for a customized multiplier and an ability to restrict the
    upper limit to some maximum value.
    """

    def __init__(self, multiplier=1, max=_utils.MAX_WAIT, exp_base=2):
        self.multiplier = multiplier
        self.max = max
        self.exp_base = exp_base

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        exp = self.exp_base ** previous_attempt_number
        result = self.multiplier * exp
        return max(0, min(result, self.max))
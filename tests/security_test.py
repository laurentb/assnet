from ass2m import security

from unittest import TestCase


class SecurityTest(TestCase):
    def test_random(self):
        assert len(security.random(42)) > len(security.random(41))
        assert len(security.armored_random(42)) > \
            len(security.armored_random(41))

        # check if it is not the end of the world
        assert security.armored_random(42) != \
            security.armored_random(42) != \
            security.armored_random(42) != \
            security.armored_random(42) != \
            security.armored_random(42) != \
            security.armored_random(42) != \
            security.armored_random(42)

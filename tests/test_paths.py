import unittest
from bardun.bardun import BardunSimplePath, BardunComplexPath


class TestSimplePath(unittest.TestCase):

    def test_simple(self):
        p = BardunSimplePath("/test")
        self.assertTrue(p.matches("/test"))

    def test_matches(self):
        p = BardunSimplePath("/test")
        self.assertEquals([], p.get_matches())


class TestComplexPath(unittest.TestCase):

    def test_simple(self):
        p = BardunComplexPath("/test")
        self.assertTrue(p.matches("/test"))
        self.assertEquals([], p.get_matches())

    def test_low_complexity_non_match(self):
        p = BardunComplexPath("/foo/:bar")
        self.assertFalse(p.matches("/foo/baz/qux"))
        self.assertEquals([], p.get_matches())

    def test_low_complexity_match(self):
        p = BardunComplexPath("/foo/:bar")
        self.assertTrue(p.matches("/foo/baz"))
        self.assertEquals(['baz'], p.get_matches())

    def test_high_complexity_match(self):
        p = BardunComplexPath("/foo/:bar/qux/:zoo/xen")
        self.assertTrue(p.matches("/foo/baz/qux/zap/xen"))
        self.assertEquals(['baz', 'zap'], p.get_matches())

    def test_high_complexity_non_match(self):
        route_path = "/foo/:bar/qux/:zoo/xen"
        given_path = "/foo/baz/qux/zap/xen/foo"
        p = BardunComplexPath(route_path)
        self.assertFalse(p.matches(given_path))

    def test_missing_key(self):
        p = BardunComplexPath("/foo/:bar/qux")
        self.assertFalse(p.matches("/foo//qux"))
        self.assertEquals([], p.get_matches())


if __name__ == '__main__':
    unittest.main()

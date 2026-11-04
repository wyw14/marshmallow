"""Tests for marshmallow.validate"""

import datetime as dt
import re
from collections import deque

import pytest

from marshmallow import ValidationError, validate


@pytest.mark.parametrize(
    "valid_url",
    [
        "http://example.org",
        "https://example.org",
        "ftp://example.org",
        "ftps://example.org",
        "http://example.co.jp",
        "http://www.example.com/a%C2%B1b",
        "http://www.example.com/~username/",
        "http://info.example.com/?fred",
        "http://xn--mgbh0fb.xn--kgbechtv/",
        "http://example.com/blue/red%3Fand+green",
        "http://www.example.com/?array%5Bkey%5D=value",
        "http://xn--rsum-bpad.example.org/",
        "http://123.45.67.8/",
        "http://123.45.67.8:8329/",
        "http://[2001:db8::ff00:42]:8329",
        "http://[2001::1]:8329",
        "http://www.example.com:8000/foo",
        "http://user@example.com",
        "http://user:pass@example.com",
        "http://:pass@example.com",
        "http://@example.com",
        "http://AZaz09-._~%2A!$&'()*+,;=:@example.com",
        "http://example.org#fragment",
        "http://user@example.com#fragment",
    ],
)
def test_url_absolute_valid(valid_url):
    validator = validate.URL(relative=False)
    assert validator(valid_url) == valid_url


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http:///example.com/",
        "https:///example.com/",
        "https://example.org\\",
        "https://example.org\n",
        "ftp:///example.com/",
        "ftps:///example.com/",
        "http//example.org",
        "http:///",
        "http:/example.org",
        "foo://example.org",
        "../icons/logo.gif",
        "http://2001:db8::ff00:42:8329",
        "http://[192.168.1.1]:8329",
        "abc",
        "..",
        "/",
        " ",
        "",
        None,
        "http://user@pass@example.com",
        "http://@pass@example.com",
        "http://@@example.com",
        "http://^@example.com",
        "http://%0G@example.com",
        "http://%@example.com",
    ],
)
def test_url_absolute_invalid(invalid_url):
    validator = validate.URL(relative=False)
    with pytest.raises(ValidationError):
        validator(invalid_url)


@pytest.mark.parametrize(
    "valid_url",
    [
        "http://example.org",
        "http://123.45.67.8/",
        "http://example.com/foo/bar/../baz",
        "https://example.com/../icons/logo.gif",
        "http://example.com/./icons/logo.gif",
        "ftp://example.com/../../../../g",
        "http://example.com/g?y/./x",
        "/foo/bar",
        "/foo?bar",
        "/foo?bar#baz",
        "#frag",
    ],
)
def test_url_relative_valid(valid_url):
    validator = validate.URL(relative=True)
    assert validator(valid_url) == valid_url


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http//example.org",
        "http://example.org\n",
        "suppliers.html",
        "../icons/logo.gif",
        "icons/logo.gif",
        "../.../g",
        "...",
        "\\",
        " ",
        "",
        None,
    ],
)
def test_url_relative_invalid(invalid_url):
    validator = validate.URL(relative=True)
    with pytest.raises(ValidationError):
        validator(invalid_url)


@pytest.mark.parametrize(
    "valid_url",
    [
        "/foo/bar",
        "/foo?bar",
        "?bar",
        "/foo?bar#baz",
        "#frag",
    ],
)
def test_url_relative_only_valid(valid_url):
    validator = validate.URL(relative=True, absolute=False)
    assert validator(valid_url) == valid_url


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http//example.org",
        "http://example.org\n",
        "suppliers.html",
        "../icons/logo.gif",
        "icons/logo.gif",
        "../.../g",
        "...",
        "\\",
        " ",
        "",
        "http://example.org",
        "http://123.45.67.8/",
        "http://example.com/foo/bar/../baz",
        "https://example.com/../icons/logo.gif",
        "http://example.com/./icons/logo.gif",
        "ftp://example.com/../../../../g",
        "http://example.com/g?y/./x",
    ],
)
def test_url_relative_only_invalid(invalid_url):
    validator = validate.URL(relative=True, absolute=False)
    with pytest.raises(ValidationError):
        validator(invalid_url)


@pytest.mark.parametrize(
    "valid_url",
    [
        "http://example.org",
        "http://123.45.67.8/",
        "http://example",
        "http://example.",
        "http://example:80",
        "http://user.name:pass.word@example",
        "http://example/foo/bar",
    ],
)
def test_url_dont_require_tld_valid(valid_url):
    validator = validate.URL(require_tld=False)
    assert validator(valid_url) == valid_url


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http//example",
        "http://example\n",
        "http://.example.org",
        "http:///foo/bar",
        "http:// /foo/bar",
        "",
        None,
    ],
)
def test_url_dont_require_tld_invalid(invalid_url):
    validator = validate.URL(require_tld=False)
    with pytest.raises(ValidationError):
        validator(invalid_url)


def test_url_custom_scheme():
    validator = validate.URL()
    # By default, ws not allowed
    url = "ws://test.test"
    with pytest.raises(ValidationError):
        validator(url)

    validator = validate.URL(schemes={"http", "https", "ws"})
    assert validator(url) == url


def test_url_custom_scheme_case_insensitive():
    validator = validate.URL(schemes={"HTTP"})
    assert validator("http://example.com") == "http://example.com"

    validator = validate.URL(schemes={"HtTp"})
    assert validator("hTtP://example.com") == "hTtP://example.com"


@pytest.mark.parametrize(
    "valid_url",
    (
        "file:///tmp/tmp1234",
        "file://localhost/tmp/tmp1234",
        "file:///C:/Users/test/file.txt",
        "file://localhost/C:/Program%20Files/file.exe",
        "file:///home/user/documents/test.pdf",
        "file:///tmp/test%20file.txt",
        "file:///",
        "file://localhost/",
        "FILE:///tmp/tmp1234",
        "FILE://localhost/tmp/tmp1234",
        "FILE:///C:/Users/test/file.txt",
        "FILE://localhost/C:/Program%20Files/file.exe",
        "FILE:///home/user/documents/test.pdf",
        "FILE:///tmp/test%20file.txt",
        "FILE:///",
        "FILE://localhost/",
    ),
)
def test_url_accepts_valid_file_urls(valid_url):
    validator = validate.URL(schemes={"file"})
    assert validator(valid_url) == valid_url


@pytest.mark.parametrize(
    "invalid_url",
    (
        "file://",
        "file:/tmp/file.txt",
        "file:tmp/file.txt",
        "file://hostname/path",
        "file:///tmp/test file.txt",
    ),
)
def test_url_rejects_invalid_file_urls(invalid_url):
    validator = validate.URL(schemes={"file"})
    with pytest.raises(ValidationError, match="Not a valid URL."):
        assert validator(invalid_url)


def test_url_relative_and_custom_schemes():
    validator = validate.URL(relative=True)
    # By default, ws not allowed
    url = "ws://test.test"
    with pytest.raises(ValidationError):
        validator(url)

    validator = validate.URL(relative=True, schemes={"http", "https", "ws"})
    assert validator(url) == url


def test_url_custom_message():
    validator = validate.URL(error="{input} ain't an URL")
    with pytest.raises(ValidationError, match="invalid ain't an URL"):
        validator("invalid")


def test_url_repr():
    assert repr(
        validate.URL(relative=False, error=None)
    ) == "<URL(relative=False, absolute=True, error={!r})>".format("Not a valid URL.")
    assert repr(
        validate.URL(relative=True, error="foo")
    ) == "<URL(relative=True, absolute=True, error={!r})>".format("foo")
    assert repr(
        validate.URL(relative=True, absolute=False, error="foo")
    ) == "<URL(relative=True, absolute=False, error={!r})>".format("foo")


def test_url_rejects_invalid_relative_usage():
    with pytest.raises(
        ValueError,
        match="URL validation cannot set both relative and absolute to False",
    ):
        validate.URL(relative=False, absolute=False)


@pytest.mark.parametrize(
    "valid_url",
    [
        "https://তৌহিদুর.বাংলা",
        "https://münchen.de",
        "https://例え.jp/path",
        "http://مثال.إختبار",
        "https://üñîçödé.com/path?q=1#frag",
        "http://www.اختبار.com:8080/path",
    ],
)
def test_url_idn_valid(valid_url):
    validator = validate.URL()
    assert validator(valid_url) == valid_url


@pytest.mark.parametrize(
    "invalid_url",
    [
        "münchen.de",
        "তৌহিদুর.বাংলা",
    ],
)
def test_url_idn_invalid(invalid_url):
    validator = validate.URL()
    with pytest.raises(ValidationError):
        validator(invalid_url)


@pytest.mark.parametrize(
    "valid_email",
    [
        "niceandsimple@example.com",
        "NiCeAnDsImPlE@eXaMpLe.CoM",
        "very.common@example.com",
        "a.little.lengthy.but.fine@a.iana-servers.net",
        "disposable.style.email.with+symbol@example.com",
        '"very.unusual.@.unusual.com"@example.com',
        "!#$%&'*+-/=?^_`{}|~@example.org",
        "niceandsimple@[64.233.160.0]",
        "niceandsimple@localhost",
        "josé@blah.com",
        "δοκ.ιμή@παράδειγμα.δοκιμή",
    ],
)
def test_email_valid(valid_email):
    validator = validate.Email()
    assert validator(valid_email) == valid_email


@pytest.mark.parametrize(
    "invalid_email",
    [
        "niceandsimple\n@example.com",
        "NiCeAnDsImPlE@eXaMpLe.CoM\n",
        'a"b(c)d,e:f;g<h>i[j\\k]l@example.com',
        'just"not"right@example.com',
        'this is"not\allowed@example.com',
        'this\\ still\\"not\\\\allowed@example.com',
        '"much.more unusual"@example.com',
        '"very.(),:;<>[]".VERY."very@\\ "very".unusual"@strange.example.com',
        '" "@example.org',
        "user@example",
        "@nouser.com",
        "example.com",
        "user",
        "",
        None,
    ],
)
def test_email_invalid(invalid_email):
    validator = validate.Email()
    with pytest.raises(ValidationError):
        validator(invalid_email)


@pytest.mark.parametrize(
    "valid_email",
    [
        "user@münchen.de",
        "user@例え.jp",
        "user@مثال.إختبار",
        "user@пример.испытание",
        "user@üñîçödé.com",
        "δοκ.ιμή@παράδειγμα.δοκιμή",
        "user@sub.münchen.de",
    ],
)
def test_email_idn_valid(valid_email):
    validator = validate.Email()
    assert validator(valid_email) == valid_email


@pytest.mark.parametrize(
    "invalid_email",
    [
        "user@-münchen.de",
        "user@münchen-.de",
        "user@münchen",
    ],
)
def test_email_idn_invalid(invalid_email):
    validator = validate.Email()
    with pytest.raises(ValidationError):
        validator(invalid_email)


def test_email_custom_message():
    validator = validate.Email(error="{input} is not an email addy.")
    with pytest.raises(ValidationError, match="invalid is not an email addy."):
        validator("invalid")


def test_email_repr():
    assert repr(validate.Email(error=None)) == "<Email(error={!r})>".format(
        "Not a valid email address."
    )
    assert repr(validate.Email(error="foo")) == "<Email(error={!r})>".format("foo")


def test_range_min():
    assert validate.Range(1, 2)(1) == 1
    assert validate.Range(0)(1) == 1
    assert validate.Range()(1) == 1
    assert validate.Range(min_inclusive=False, max_inclusive=False)(1) == 1
    assert validate.Range(1, 1)(1) == 1

    with pytest.raises(ValidationError, match="Must be greater than or equal to 2"):
        validate.Range(2, 3)(1)
    with pytest.raises(ValidationError, match="Must be greater than or equal to 2"):
        validate.Range(2)(1)
    with pytest.raises(ValidationError, match="Must be greater than 1"):
        validate.Range(1, 2, min_inclusive=False, max_inclusive=True, error=None)(1)
    with pytest.raises(ValidationError, match="less than 1"):
        validate.Range(1, 1, min_inclusive=True, max_inclusive=False, error=None)(1)


def test_range_max():
    assert validate.Range(1, 2)(2) == 2
    assert validate.Range(None, 2)(2) == 2
    assert validate.Range()(2) == 2
    assert validate.Range(min_inclusive=False, max_inclusive=False)(2) == 2
    assert validate.Range(2, 2)(2) == 2

    with pytest.raises(ValidationError, match="less than or equal to 1"):
        validate.Range(0, 1)(2)
    with pytest.raises(ValidationError, match="less than or equal to 1"):
        validate.Range(None, 1)(2)
    with pytest.raises(ValidationError, match="less than 2"):
        validate.Range(1, 2, min_inclusive=True, max_inclusive=False, error=None)(2)
    with pytest.raises(ValidationError, match="greater than 2"):
        validate.Range(2, 2, min_inclusive=False, max_inclusive=True, error=None)(2)


def test_range_custom_message():
    v = validate.Range(2, 3, error="{input} is not between {min} and {max}")
    with pytest.raises(ValidationError, match="1 is not between 2 and 3"):
        v(1)

    v = validate.Range(2, None, error="{input} is less than {min}")
    with pytest.raises(ValidationError, match="1 is less than 2"):
        v(1)

    v = validate.Range(None, 3, error="{input} is greater than {max}")
    with pytest.raises(ValidationError, match="4 is greater than 3"):
        v(4)


def test_range_repr():
    assert (
        repr(
            validate.Range(
                min=None, max=None, error=None, min_inclusive=True, max_inclusive=True
            )
        )
        == "<Range(min=None, max=None, min_inclusive=True, max_inclusive=True, error=None)>"
    )
    assert (
        repr(
            validate.Range(
                min=1, max=3, error="foo", min_inclusive=False, max_inclusive=False
            )
        )
        == "<Range(min=1, max=3, min_inclusive=False, max_inclusive=False, error={!r})>".format(
            "foo"
        )
    )


def test_length_min():
    assert validate.Length(3, 5)("foo") == "foo"
    assert validate.Length(3, 5)([1, 2, 3]) == [1, 2, 3]
    assert validate.Length(0)("a") == "a"
    assert validate.Length(0)([1]) == [1]
    assert validate.Length()("") == ""
    assert validate.Length()([]) == []
    assert validate.Length(1, 1)("a") == "a"
    assert validate.Length(1, 1)([1]) == [1]

    with pytest.raises(ValidationError):
        validate.Length(4, 5)("foo")
    with pytest.raises(ValidationError):
        validate.Length(4, 5)([1, 2, 3])
    with pytest.raises(ValidationError):
        validate.Length(5)("foo")
    with pytest.raises(ValidationError):
        validate.Length(5)([1, 2, 3])


def test_length_max():
    assert validate.Length(1, 3)("foo") == "foo"
    assert validate.Length(1, 3)([1, 2, 3]) == [1, 2, 3]
    assert validate.Length(None, 1)("a") == "a"
    assert validate.Length(None, 1)([1]) == [1]
    assert validate.Length()("") == ""
    assert validate.Length()([]) == []
    assert validate.Length(2, 2)("ab") == "ab"
    assert validate.Length(2, 2)([1, 2]) == [1, 2]

    with pytest.raises(ValidationError):
        validate.Length(1, 2)("foo")
    with pytest.raises(ValidationError):
        validate.Length(1, 2)([1, 2, 3])
    with pytest.raises(ValidationError):
        validate.Length(None, 2)("foo")
    with pytest.raises(ValidationError):
        validate.Length(None, 2)([1, 2, 3])


def test_length_equal():
    assert validate.Length(equal=3)("foo") == "foo"
    assert validate.Length(equal=3)([1, 2, 3]) == [1, 2, 3]
    assert validate.Length(equal=None)("") == ""
    assert validate.Length(equal=None)([]) == []

    with pytest.raises(ValidationError):
        validate.Length(equal=2)("foo")
    with pytest.raises(ValidationError):
        validate.Length(equal=2)([1, 2, 3])
    error_message = "The `equal` parameter was provided, maximum or minimum parameter must not be provided"
    with pytest.raises(ValueError, match=error_message):
        validate.Length(1, None, equal=3)("foo")
    with pytest.raises(ValueError, match=error_message):
        validate.Length(None, 5, equal=3)("foo")
    with pytest.raises(ValueError, match=error_message):
        validate.Length(1, 5, equal=3)("foo")


def test_length_custom_message():
    v = validate.Length(5, 6, error="{input} is not between {min} and {max}")
    with pytest.raises(ValidationError, match="foo is not between 5 and 6"):
        v("foo")

    v = validate.Length(5, None, error="{input} is shorter than {min}")
    with pytest.raises(ValidationError, match="foo is shorter than 5"):
        v("foo")

    v = validate.Length(None, 2, error="{input} is longer than {max}")
    with pytest.raises(ValidationError, match="foo is longer than 2"):
        v("foo")

    v = validate.Length(None, None, equal=4, error="{input} does not have {equal}")
    with pytest.raises(ValidationError, match="foo does not have 4"):
        v("foo")


def test_length_repr():
    assert (
        repr(validate.Length(min=None, max=None, error=None, equal=None))
        == "<Length(min=None, max=None, equal=None, error=None)>"
    )
    assert repr(
        validate.Length(min=1, max=3, error="foo", equal=None)
    ) == "<Length(min=1, max=3, equal=None, error={!r})>".format("foo")
    assert repr(
        validate.Length(min=None, max=None, error="foo", equal=5)
    ) == "<Length(min=None, max=None, equal=5, error={!r})>".format("foo")


def test_equal():
    assert validate.Equal("a")("a") == "a"
    assert validate.Equal(1)(1) == 1
    assert validate.Equal([1])([1]) == [1]

    with pytest.raises(ValidationError):
        validate.Equal("b")("a")
    with pytest.raises(ValidationError):
        validate.Equal(2)(1)
    with pytest.raises(ValidationError):
        validate.Equal([2])([1])


def test_equal_custom_message():
    v = validate.Equal("a", error="{input} is not equal to {other}.")
    with pytest.raises(ValidationError, match="b is not equal to a."):
        v("b")


def test_equal_repr():
    assert repr(
        validate.Equal(comparable=123, error=None)
    ) == "<Equal(comparable=123, error={!r})>".format("Must be equal to {other}.")
    assert repr(
        validate.Equal(comparable=123, error="foo")
    ) == "<Equal(comparable=123, error={!r})>".format("foo")


def test_regexp_str():
    assert validate.Regexp(r"a")("a") == "a"
    assert validate.Regexp(r"\w")("_") == "_"
    assert validate.Regexp(r"\s")(" ") == " "
    assert validate.Regexp(r"1")("1") == "1"
    assert validate.Regexp(r"[0-9]+")("1") == "1"
    assert validate.Regexp(r"a", re.IGNORECASE)("A") == "A"

    with pytest.raises(ValidationError):
        validate.Regexp(r"[0-9]+")("a")
    with pytest.raises(ValidationError):
        validate.Regexp(r"[a-z]+")("1")
    with pytest.raises(ValidationError):
        validate.Regexp(r"a")("A")


def test_regexp_compile():
    assert validate.Regexp(re.compile(r"a"))("a") == "a"
    assert validate.Regexp(re.compile(r"\w"))("_") == "_"
    assert validate.Regexp(re.compile(r"\s"))(" ") == " "
    assert validate.Regexp(re.compile(r"1"))("1") == "1"
    assert validate.Regexp(re.compile(r"[0-9]+"))("1") == "1"
    assert validate.Regexp(re.compile(r"a", re.IGNORECASE))("A") == "A"
    assert validate.Regexp(re.compile(r"a", re.IGNORECASE), re.IGNORECASE)("A") == "A"

    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r"[0-9]+"))("a")
    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r"[a-z]+"))("1")
    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r"a"))("A")
    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r"a"), re.IGNORECASE)("A")


def test_regexp_custom_message():
    rex = r"[0-9]+"
    v = validate.Regexp(rex, error="{input} does not match {regex}")
    with pytest.raises(ValidationError, match="a does not match"):
        v("a")


def test_regexp_repr():
    assert repr(
        validate.Regexp(regex="abc", flags=0, error=None)
    ) == "<Regexp(regex={!r}, error={!r})>".format(
        re.compile("abc"), "String does not match expected pattern."
    )
    assert repr(
        validate.Regexp(regex="abc", flags=re.IGNORECASE, error="foo")
    ) == "<Regexp(regex={!r}, error={!r})>".format(
        re.compile("abc", re.IGNORECASE), "foo"
    )


def test_predicate():
    class Dummy:
        def _true(self):
            return True

        def _false(self):
            return False

        def _list(self):
            return [1, 2, 3]

        def _empty(self):
            return []

        def _identity(self, arg):
            return arg

    d = Dummy()

    assert validate.Predicate("_true")(d) == d
    assert validate.Predicate("_list")(d) == d
    assert validate.Predicate("_identity", arg=True)(d) == d
    assert validate.Predicate("_identity", arg=1)(d) == d
    assert validate.Predicate("_identity", arg="abc")(d) == d

    with pytest.raises(ValidationError, match="Invalid input."):
        validate.Predicate("_false")(d)
    with pytest.raises(ValidationError):
        validate.Predicate("_empty")(d)
    with pytest.raises(ValidationError):
        validate.Predicate("_identity", arg=False)(d)
    with pytest.raises(ValidationError):
        validate.Predicate("_identity", arg=0)(d)
    with pytest.raises(ValidationError):
        validate.Predicate("_identity", arg="")(d)


def test_predicate_custom_message():
    class Dummy:
        def _false(self):
            return False

        def __str__(self):
            return "Dummy"

    d = Dummy()
    with pytest.raises(ValidationError, match="Dummy._false is invalid!"):
        validate.Predicate("_false", error="{input}.{method} is invalid!")(d)


def test_predicate_repr():
    assert repr(
        validate.Predicate(method="foo", error=None)
    ) == "<Predicate(method={!r}, kwargs={!r}, error={!r})>".format(
        "foo", {}, "Invalid input."
    )
    assert repr(
        validate.Predicate(method="foo", error="bar", zoo=1)
    ) == "<Predicate(method={!r}, kwargs={!r}, error={!r})>".format(
        "foo", {"zoo": 1}, "bar"
    )


def test_noneof():
    assert validate.NoneOf([1, 2, 3])(4) == 4
    assert validate.NoneOf("abc")("d") == "d"
    assert validate.NoneOf("")([]) == []
    assert validate.NoneOf([])("") == ""
    assert validate.NoneOf([])([]) == []
    assert validate.NoneOf([1, 2, 3])(None) is None

    with pytest.raises(ValidationError, match="Invalid input."):
        validate.NoneOf([1, 2, 3])(3)
    with pytest.raises(ValidationError):
        validate.NoneOf("abc")("c")
    with pytest.raises(ValidationError):
        validate.NoneOf([1, 2, None])(None)
    with pytest.raises(ValidationError):
        validate.NoneOf("")("")


def test_noneof_custom_message():
    with pytest.raises(ValidationError, match="<not valid>"):
        validate.NoneOf([1, 2], error="<not valid>")(1)

    none_of = validate.NoneOf([1, 2], error="{input} cannot be one of {values}")
    with pytest.raises(ValidationError, match="1 cannot be one of 1, 2"):
        none_of(1)


def test_noneof_repr():
    assert repr(
        validate.NoneOf(iterable=[1, 2, 3], error=None)
    ) == "<NoneOf(iterable=[1, 2, 3], error={!r})>".format("Invalid input.")
    assert repr(
        validate.NoneOf(iterable=[1, 2, 3], error="foo")
    ) == "<NoneOf(iterable=[1, 2, 3], error={!r})>".format("foo")


def test_oneof():
    assert validate.OneOf([1, 2, 3])(2) == 2
    assert validate.OneOf("abc")("b") == "b"
    assert validate.OneOf("")("") == ""
    assert validate.OneOf(dict(a=0, b=1))("a") == "a"
    assert validate.OneOf((1, 2, None))(None) is None

    with pytest.raises(ValidationError, match="Must be one of: 1, 2, 3."):
        validate.OneOf([1, 2, 3])(4)
    with pytest.raises(ValidationError):
        validate.OneOf("abc")("d")
    with pytest.raises(ValidationError):
        validate.OneOf((1, 2, 3))(None)
    with pytest.raises(ValidationError):
        validate.OneOf([])([])
    with pytest.raises(ValidationError):
        validate.OneOf(())(())
    with pytest.raises(ValidationError):
        validate.OneOf(dict(a=0, b=1))(0)
    with pytest.raises(ValidationError):
        validate.OneOf("123")(1)


def test_oneof_options():
    oneof = validate.OneOf([1, 2, 3], ["one", "two", "three"])
    expected = [("1", "one"), ("2", "two"), ("3", "three")]
    assert list(oneof.options()) == expected

    oneof = validate.OneOf([1, 2, 3], ["one", "two"])
    expected = [("1", "one"), ("2", "two"), ("3", "")]
    assert list(oneof.options()) == expected

    oneof = validate.OneOf([1, 2], ["one", "two", "three"])
    expected = [("1", "one"), ("2", "two")]
    assert list(oneof.options()) == expected

    oneof = validate.OneOf([1, 2])
    expected = [("1", ""), ("2", "")]
    assert list(oneof.options()) == expected

    # Empty choices with extra labels should produce no options
    oneof = validate.OneOf(choices=[], labels=["extra"])
    assert list(oneof.options()) == []


def test_oneof_text():
    oneof = validate.OneOf([1, 2, 3], ["one", "two", "three"])
    assert oneof.choices_text == "1, 2, 3"
    assert oneof.labels_text == "one, two, three"

    oneof = validate.OneOf([1], ["one"])
    assert oneof.choices_text == "1"
    assert oneof.labels_text == "one"

    oneof = validate.OneOf(dict(a=0, b=1))
    assert ", ".join(sorted(oneof.choices_text.split(", "))) == "a, b"
    assert oneof.labels_text == ""


def test_oneof_custom_message():
    oneof = validate.OneOf([1, 2, 3], error="{input} is not one of {choices}")
    expected = "4 is not one of 1, 2, 3"
    with pytest.raises(ValidationError):
        oneof(4)
    assert expected in str(expected)

    oneof = validate.OneOf(
        [1, 2, 3], ["one", "two", "three"], error="{input} is not one of {labels}"
    )
    expected = "4 is not one of one, two, three"
    with pytest.raises(ValidationError):
        oneof(4)
    assert expected in str(expected)


def test_oneof_repr():
    assert repr(
        validate.OneOf(choices=[1, 2, 3], labels=None, error=None)
    ) == "<OneOf(choices=[1, 2, 3], labels=[], error={!r})>".format(
        "Must be one of: {choices}."
    )
    assert repr(
        validate.OneOf(choices=[1, 2, 3], labels=["a", "b", "c"], error="foo")
    ) == "<OneOf(choices=[1, 2, 3], labels={!r}, error={!r})>".format(
        ["a", "b", "c"], "foo"
    )


def test_containsonly_in_list():
    assert validate.ContainsOnly([])([]) == []
    assert validate.ContainsOnly([1, 2, 3])([1]) == [1]
    assert validate.ContainsOnly([1, 1, 2])([1, 1]) == [1, 1]
    assert validate.ContainsOnly([1, 2, 3])([1, 2]) == [1, 2]
    assert validate.ContainsOnly([1, 2, 3])([2, 1]) == [2, 1]
    assert validate.ContainsOnly([1, 2, 3])([1, 2, 3]) == [1, 2, 3]
    assert validate.ContainsOnly([1, 2, 3])([3, 1, 2]) == [3, 1, 2]
    assert validate.ContainsOnly([1, 2, 3])([2, 3, 1]) == [2, 3, 1]
    assert validate.ContainsOnly([1, 2, 3])([1, 2, 3, 1]) == [1, 2, 3, 1]
    assert validate.ContainsOnly([1, 2, 3])([]) == []

    with pytest.raises(
        ValidationError,
        match="One or more of the choices you made was not in: 1, 2, 3.",
    ):
        validate.ContainsOnly([1, 2, 3])([4])
    with pytest.raises(ValidationError):
        validate.ContainsOnly([])([1])


def test_contains_only_unhashable_types():
    assert validate.ContainsOnly([[1], [2], [3]])([[1]]) == [[1]]
    assert validate.ContainsOnly([[1], [1], [2]])([[1], [1]]) == [[1], [1]]
    assert validate.ContainsOnly([[1], [2], [3]])([[1], [2]]) == [[1], [2]]
    assert validate.ContainsOnly([[1], [2], [3]])([[2], [1]]) == [[2], [1]]
    assert validate.ContainsOnly([[1], [2], [3]])([[1], [2], [3]]) == [[1], [2], [3]]
    assert validate.ContainsOnly([[1], [2], [3]])([[3], [1], [2]]) == [[3], [1], [2]]
    assert validate.ContainsOnly([[1], [2], [3]])([[2], [3], [1]]) == [[2], [3], [1]]
    assert validate.ContainsOnly([[1], [2], [3]])([]) == []

    with pytest.raises(ValidationError):
        validate.ContainsOnly([[1], [2], [3]])([[4]])
    with pytest.raises(ValidationError):
        validate.ContainsOnly([])([1])


def test_containsonly_in_tuple():
    assert validate.ContainsOnly(())(()) == ()
    assert validate.ContainsOnly((1, 2, 3))((1,)) == (1,)
    assert validate.ContainsOnly((1, 1, 2))((1, 1)) == (1, 1)
    assert validate.ContainsOnly((1, 2, 3))((1, 2)) == (1, 2)
    assert validate.ContainsOnly((1, 2, 3))((2, 1)) == (2, 1)
    assert validate.ContainsOnly((1, 2, 3))((1, 2, 3)) == (1, 2, 3)
    assert validate.ContainsOnly((1, 2, 3))((3, 1, 2)) == (3, 1, 2)
    assert validate.ContainsOnly((1, 2, 3))((2, 3, 1)) == (2, 3, 1)
    assert validate.ContainsOnly((1, 2, 3))(()) == tuple()
    with pytest.raises(ValidationError):
        validate.ContainsOnly((1, 2, 3))((4,))
    with pytest.raises(ValidationError):
        validate.ContainsOnly(())((1,))


def test_contains_only_in_string():
    assert validate.ContainsOnly("")("") == ""
    assert validate.ContainsOnly("abc")("a") == "a"
    assert validate.ContainsOnly("aab")("aa") == "aa"
    assert validate.ContainsOnly("abc")("ab") == "ab"
    assert validate.ContainsOnly("abc")("ba") == "ba"
    assert validate.ContainsOnly("abc")("abc") == "abc"
    assert validate.ContainsOnly("abc")("cab") == "cab"
    assert validate.ContainsOnly("abc")("bca") == "bca"
    assert validate.ContainsOnly("abc")("") == ""

    with pytest.raises(ValidationError):
        validate.ContainsOnly("abc")("d")
    with pytest.raises(ValidationError):
        validate.ContainsOnly("")("a")


def test_containsonly_custom_message():
    containsonly = validate.ContainsOnly(
        [1, 2, 3], error="{input} is not one of {choices}"
    )
    expected = "4, 5 is not one of 1, 2, 3"
    with pytest.raises(ValidationError):
        containsonly([4, 5])
    assert expected in str(expected)

    containsonly = validate.ContainsOnly(
        [1, 2, 3], ["one", "two", "three"], error="{input} is not one of {labels}"
    )
    expected = "4, 5 is not one of one, two, three"
    with pytest.raises(ValidationError):
        containsonly([4, 5])
    assert expected in str(expected)


def test_containsonly_repr():
    assert repr(
        validate.ContainsOnly(choices=[1, 2, 3], labels=None, error=None)
    ) == "<ContainsOnly(choices=[1, 2, 3], labels=[], error={!r})>".format(
        "One or more of the choices you made was not in: {choices}."
    )
    assert repr(
        validate.ContainsOnly(choices=[1, 2, 3], labels=["a", "b", "c"], error="foo")
    ) == "<ContainsOnly(choices=[1, 2, 3], labels={!r}, error={!r})>".format(
        ["a", "b", "c"], "foo"
    )


def test_containsnoneof_error_message():
    with pytest.raises(
        ValidationError, match="One or more of the choices you made was in: 1"
    ):
        validate.ContainsNoneOf([1])([1])

    with pytest.raises(
        ValidationError, match="One or more of the choices you made was in: 1, 2, 3"
    ):
        validate.ContainsNoneOf([1, 2, 3])([1])

    with pytest.raises(
        ValidationError, match="One or more of the choices you made was in: one, two"
    ):
        validate.ContainsNoneOf(["one", "two"])(["one"])

    with pytest.raises(
        ValidationError, match="One or more of the choices you made was in: @, !, &, ?"
    ):
        validate.ContainsNoneOf("@!&?")("@")


def test_containsnoneof_in_list():
    assert validate.ContainsNoneOf([])([]) == []
    assert validate.ContainsNoneOf([])([1, 2, 3]) == [1, 2, 3]
    assert validate.ContainsNoneOf([4])([1, 2, 3]) == [1, 2, 3]
    assert validate.ContainsNoneOf([2])([1, 3, 4]) == [1, 3, 4]
    assert validate.ContainsNoneOf([1, 2, 3])([4]) == [4]
    assert validate.ContainsNoneOf([4])([1, 1, 1, 1]) == [1, 1, 1, 1]

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf([1])([1, 2, 3])

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf([1, 1, 1])([1, 2, 3])

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf([1, 2])([1, 2])

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf([1])([1, 1, 1, 1])


def test_containsnoneof_unhashable_types():
    assert validate.ContainsNoneOf([[1], [2], [3]])([]) == []
    assert validate.ContainsNoneOf([[1], [2], [3]])([[4]]) == [[4]]
    assert validate.ContainsNoneOf([[1], [2], [3]])([[4], [4]]) == [[4], [4]]
    assert validate.ContainsNoneOf([[1], [2], [3]])([[4], [5]]) == [[4], [5]]

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf([[1], [2], [3]])([[1]])

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf([[1], [2], [3]])([[1], [2]])

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf([[1], [2], [3]])([[2], [1]])

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf([[1], [2], [3]])([[1], [2], [3]])

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf([[1], [2], [3]])([[3], [2], [1]])

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf([[1], [2], [3]])([[2], [3], [1]])


def test_containsnoneof_in_tuple():
    assert validate.ContainsNoneOf(())(()) == ()
    assert validate.ContainsNoneOf(())((1, 2, 3)) == (1, 2, 3)
    assert validate.ContainsNoneOf((4,))((1, 2, 3)) == (1, 2, 3)
    assert validate.ContainsNoneOf((2,))((1, 3, 4)) == (1, 3, 4)
    assert validate.ContainsNoneOf((1, 2, 3))((4,)) == (4,)
    assert validate.ContainsNoneOf((4,))((1, 1, 1, 1)) == (1, 1, 1, 1)

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf((1,))((1, 2, 3))

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf((1, 1, 1))((1, 2, 3))

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf((1, 2))((1, 2))

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf((1,))((1, 1, 1, 1))


def test_containsnoneof_in_string():
    assert validate.ContainsNoneOf("")("") == ""
    assert validate.ContainsNoneOf("")("abc") == "abc"
    assert validate.ContainsNoneOf("d")("abc") == "abc"
    assert validate.ContainsNoneOf("b")("acd") == "acd"
    assert validate.ContainsNoneOf("abc")("d") == "d"
    assert validate.ContainsNoneOf("d")("aaaa") == "aaaa"

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf("a")("abc")

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf("aaa")("abc")

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf("ab")("ab")

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf("a")("aaaa")


def test_containsnoneof_custom_message():
    validator = validate.ContainsNoneOf(
        [1, 2, 3], error="{input} was in the banned list: {values}"
    )
    expected = "1 was in the banned list: 1, 2, 3"
    with pytest.raises(ValidationError, match=expected):
        validator([1])


def test_containsnoneof_mixing_types():
    with pytest.raises(ValidationError):
        validate.ContainsNoneOf("abc")(["a"])

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf(["a", "b", "c"])("a")

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf((1, 2, 3))([1])

    with pytest.raises(ValidationError):
        validate.ContainsNoneOf([1, 2, 3])((1,))


def is_even(value):
    if value % 2 != 0:
        raise ValidationError("Not an even value.")


def test_and():
    validator = validate.And(validate.Range(min=0), is_even)
    assert validator(2)
    with pytest.raises(ValidationError) as excinfo:
        validator(-1)
    errors = excinfo.value.messages
    assert errors == ["Must be greater than or equal to 0.", "Not an even value."]

    validator_with_composition = validate.And(validator, validate.Range(max=6))
    assert validator_with_composition(4)
    with pytest.raises(ValidationError) as excinfo:
        validator_with_composition(7)

    errors = excinfo.value.messages
    assert errors == ["Not an even value.", "Must be less than or equal to 6."]


def test_monotonic_empty_and_single_element_pass():
    assert validate.Monotonic()([]) == []
    assert validate.Monotonic(strict=True)(()) == ()
    assert validate.Monotonic(increasing=False)([1]) == [1]
    assert validate.Monotonic(strict=True, increasing=False)(("a",)) == ("a",)


def test_monotonic_key_not_called_for_short_sequences():
    def fail_key(item):
        raise AssertionError("key should not be called")

    assert validate.Monotonic(key=fail_key)([]) == []
    assert validate.Monotonic(key=fail_key)([1]) == [1]


def test_monotonic_increasing():
    validator = validate.Monotonic()
    assert validator([1, 2, 3]) == [1, 2, 3]
    assert validator((-2, -1, 0, 1)) == (-2, -1, 0, 1)
    assert validator([1, 1, 2, 2, 3]) == [1, 1, 2, 2, 3]
    assert validator([1.0, 1, 1.5, 2]) == [1.0, 1, 1.5, 2]
    assert validator(deque([1, 2, 3])) == deque([1, 2, 3])
    assert validator(range(3)) == range(3)
    assert validator(["a", "b", "c"]) == ["a", "b", "c"]

    with pytest.raises(ValidationError, match="non-decreasing"):
        validator([1, 2, 0])
    with pytest.raises(ValidationError):
        validator([3, 2, 1])
    with pytest.raises(ValidationError):
        validator([1, 2, 3, 3, 2])


def test_monotonic_strict_increasing():
    validator = validate.Monotonic(strict=True)
    assert validator([1, 2, 3]) == [1, 2, 3]
    assert validator((1, 2)) == (1, 2)

    with pytest.raises(ValidationError, match="strictly increasing"):
        validator([1, 1, 2])
    with pytest.raises(ValidationError):
        validator([1, 2, 2, 3])
    with pytest.raises(ValidationError):
        validator([3, 2])


def test_monotonic_decreasing():
    validator = validate.Monotonic(increasing=False)
    assert validator([3, 2, 1]) == [3, 2, 1]
    assert validator([3, 3, 2, 2, 1]) == [3, 3, 2, 2, 1]
    assert validator(("c", "b", "a")) == ("c", "b", "a")

    with pytest.raises(ValidationError, match="non-increasing"):
        validator([1, 2, 0])
    with pytest.raises(ValidationError):
        validator([1, 2, 3])


def test_monotonic_strict_decreasing():
    validator = validate.Monotonic(increasing=False, strict=True)
    assert validator([3, 2, 1]) == [3, 2, 1]

    with pytest.raises(ValidationError, match="strictly decreasing"):
        validator([3, 3, 1])
    with pytest.raises(ValidationError):
        validator([3, 2, 2])
    with pytest.raises(ValidationError):
        validator([1, 2])


def test_monotonic_first_violating_pair_is_reported():
    # [2, 0] is the first offending pair, at zero-based pair index 1
    with pytest.raises(
        ValidationError,
        match=(r"0 at index 2 is smaller than 2 at index 1"),
    ):
        validate.Monotonic()([1, 2, 0, 5])

    # strict increasing: equality at indices 2 and 3 is the first violation
    with pytest.raises(
        ValidationError,
        match=r"3 at index 3 is not greater than 3 at index 2",
    ):
        validate.Monotonic(strict=True)([1, 2, 3, 3, 4])

    with pytest.raises(
        ValidationError,
        match=r"3 at index 2 is greater than 1 at index 1",
    ):
        validate.Monotonic(increasing=False)([5, 1, 3, 0])


def test_monotonic_returns_input_unchanged():
    validator = validate.Monotonic(strict=True)
    data = [1, 2, 3]
    assert validator(data) is data

    data = [1, 1, 2]
    assert validate.Monotonic()(data) is data

    pair = (3, 2, 1)
    assert validate.Monotonic(increasing=False)(pair) is pair

    # elements are neither replaced nor copied
    a = object()
    b = object()
    result = validate.Monotonic(key=lambda _: 1)([a, b])
    assert result[0] is a
    assert result[1] is b


def test_monotonic_with_key():
    validator = validate.Monotonic(strict=True, key=str.lower)
    assert validator(["a", "B", "c"]) == ["a", "B", "c"]
    with pytest.raises(ValidationError):
        # without the key, uppercase "B" sorts before lowercase "a"
        validate.Monotonic(strict=True)(["a", "B", "c"])

    records = [
        {"name": "alice", "age": 30},
        {"name": "bob", "age": 40},
        {"name": "carol", "age": 50},
    ]
    by_age = validate.Monotonic(key=lambda item: item["age"])
    assert by_age(records) is records
    with pytest.raises(ValidationError, match=r"index 2"):
        by_age(
            [
                {"name": "alice", "age": 30},
                {"name": "carol", "age": 50},
                {"name": "bob", "age": 40},
            ]
        )

    by_age_strict = validate.Monotonic(strict=True, key=lambda item: item["age"])
    with pytest.raises(ValidationError):
        by_age_strict(
            [
                {"name": "alice", "age": 30},
                {"name": "bob", "age": 30},
            ]
        )

    # Jan 5 2020 (Sunday, isoweekday 7) then Jan 1 (Wednesday, 3): the
    # dates themselves are increasing but their weekday keys are decreasing
    dates = [
        dt.datetime(2020, 1, 5, tzinfo=dt.timezone.utc),
        dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc),
    ]
    assert (
        validate.Monotonic(increasing=False, key=dt.datetime.isoweekday)(dates) is dates
    )


def test_monotonic_incomparable_elements_become_validation_error():
    with pytest.raises(ValidationError, match=r"indices 0 and 1") as excinfo:
        validate.Monotonic()([1, "a"])
    assert isinstance(excinfo.value.__cause__, TypeError)
    assert excinfo.value.messages == [
        "Elements at indices 0 and 1 cannot be compared: 1 and a."
    ]

    # first incomparable pair is reported, even though an ordering violation
    # occurs later
    with pytest.raises(ValidationError, match=r"indices 1 and 2"):
        validate.Monotonic()([1, 2, "a", 0])

    with pytest.raises(ValidationError, match=r"indices 0 and 1"):
        validate.Monotonic(increasing=False)([None, 1])


def test_monotonic_incomparable_keys_become_validation_error():
    with pytest.raises(ValidationError, match=r"indices 0 and 1") as excinfo:
        validate.Monotonic(key=lambda item: item["n"])([{"n": 1}, {"n": "a"}])
    assert isinstance(excinfo.value.__cause__, TypeError)

    with pytest.raises(ValidationError, match=r"indices 2 and 3"):
        validate.Monotonic(key=lambda item: item["n"])(
            [{"n": 1}, {"n": 2}, {"n": 3}, {"n": "x"}]
        )


def test_monotonic_key_other_exceptions_propagate():
    def boom(item):
        raise ValueError("key failure")

    with pytest.raises(ValueError, match="key failure"):
        validate.Monotonic(key=boom)([1, 2])

    class CustomKeyError(RuntimeError):
        pass

    def raise_custom(item):
        raise CustomKeyError

    with pytest.raises(CustomKeyError):
        validate.Monotonic(key=raise_custom)([1, 2, 3])

    with pytest.raises(KeyError):
        validate.Monotonic(key=lambda item: item["n"])([{}, {"n": 1}])

    # a TypeError raised by the key function itself (as opposed to the
    # comparison) propagates untouched
    with pytest.raises(TypeError):
        validate.Monotonic(key=lambda item: item + 1)([None, 1])


def test_monotonic_rejects_strings_and_bytes():
    with pytest.raises(ValidationError, match="Strings and bytes"):
        validate.Monotonic()("abcd")
    with pytest.raises(ValidationError):
        validate.Monotonic(strict=True)("aabc")
    with pytest.raises(ValidationError):
        validate.Monotonic()(b"abcd")
    with pytest.raises(ValidationError):
        validate.Monotonic()(bytearray(b"abcd"))
    with pytest.raises(ValidationError):
        validate.Monotonic()(memoryview(b"abcd"))


def test_monotonic_rejects_one_shot_iterators_without_consuming_them():
    gen = (number for number in range(3))
    with pytest.raises(ValidationError, match="re-iterable sequence"):
        validate.Monotonic()(gen)
    # the generator must not have been consumed by validation
    assert next(gen) == 0
    assert list(gen) == [1, 2]

    iterator = iter([1, 2, 3])
    with pytest.raises(ValidationError):
        validate.Monotonic(strict=True)(iterator)
    assert next(iterator) == 1

    paired = zip([1, 2], [3, 4])  # noqa: B905
    with pytest.raises(ValidationError):
        validate.Monotonic()(paired)
    assert list(paired) == [(1, 3), (2, 4)]

    with pytest.raises(ValidationError):
        validate.Monotonic()(map(lambda n: n, [1, 2]))  # noqa: C417
    with pytest.raises(ValidationError):
        validate.Monotonic()({1, 2, 3})
    with pytest.raises(ValidationError):
        validate.Monotonic()(frozenset({1, 2, 3}))
    with pytest.raises(ValidationError):
        validate.Monotonic()({1: 2, 3: 4})
    with pytest.raises(ValidationError):
        validate.Monotonic()(123)
    with pytest.raises(ValidationError):
        validate.Monotonic()(None)


def test_monotonic_accepts_indexed_re_iterable_sequences():
    class IndexableIterable:
        def __init__(self, values):
            self._values = values

        def __len__(self):
            return len(self._values)

        def __getitem__(self, index):
            return self._values[index]

    sequence = IndexableIterable([1, 2, 3])
    assert validate.Monotonic()(sequence) is sequence
    with pytest.raises(ValidationError):
        validate.Monotonic()(IndexableIterable([1, 0]))


def test_monotonic_custom_message():
    validator = validate.Monotonic(
        error="{previous} before {current}; pair starts at index {index}"
    )
    with pytest.raises(
        ValidationError,
        match=r"2 before 0; pair starts at index 1",
    ):
        validator([1, 2, 0])

    validator = validate.Monotonic(
        increasing=False,
        strict=True,
        error="bad pair {index}/{next_index}: {previous} {current}",
    )
    with pytest.raises(ValidationError, match=r"bad pair 0/1: 3 3"):
        validator([3, 3, 1])

    # the custom message also applies when elements cannot be compared
    with pytest.raises(ValidationError, match=r"bad pair 0/1: 1 a"):
        validate.Monotonic(error="bad pair {index}/{next_index}: {previous} {current}")(
            [1, "a"]
        )


def test_monotonic_repr():
    assert (
        repr(validate.Monotonic())
        == "<Monotonic(increasing=True, strict=False, key=None, error=None)>"
    )
    assert repr(
        validate.Monotonic(increasing=False, strict=True, error="bad order")
    ) == (
        "<Monotonic(increasing=False, strict=True, key=None, error={!r})>".format(
            "bad order"
        )
    )
    assert "key=<built-in function abs>" in repr(validate.Monotonic(key=abs))

# -*- coding: utf-8 -*-
# perimeter tests
import datetime

from django.contrib.auth.models import User, AnonymousUser
from django.core.cache import cache
from django.core.exceptions import ValidationError, MiddlewareNotUsed, PermissionDenied
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory, override_settings
from django.utils.timezone import now

from perimeter.forms import GatewayForm
from perimeter.middleware import (
    PerimeterAccessMiddleware,
    bypass_perimeter,
    get_request_token
)
from perimeter.models import (
    AccessToken,
    AccessTokenUse,
    default_expiry,
    EmptyToken
)
from perimeter.settings import PERIMETER_DEFAULT_EXPIRY

TODAY = now().date()
YESTERDAY = TODAY - datetime.timedelta(days=1)
TOMORROW = TODAY + datetime.timedelta(days=1)


class EmptyTokenTests(TestCase):

    def test_is_valid(self):
        """EmptyToken should always be invalid."""
        token = EmptyToken()
        self.assertFalse(token.is_valid)


class AccessTokenManagerTests(TestCase):

    def test_create_with_token(self):
        """If a token is passed in to create_access_token, it's used."""
        token = AccessToken.objects.create_access_token(token='x')
        self.assertEqual(token, AccessToken.objects.get())
        self.assertTrue(token, 'x')

    def test_create_without_token(self):
        """If no token is passed in to create_access_token, a random one is used."""
        token = AccessToken.objects.create_access_token()
        self.assertEqual(token, AccessToken.objects.get())
        self.assertTrue(len(token.token), 10)

    def test_get_access_token(self):
        """Test the caching works."""
        token = AccessToken.objects.create_access_token()
        cache.clear()
        self.assertIsNone(cache.get(token.cache_key))
        token2 = AccessToken.objects.get_access_token(token.token)
        self.assertEqual(token, token2)
        self.assertIsNotNone(cache.get(token.cache_key))

class AccessTokenTests(TestCase):

    def test_default_expiry(self):
        self.assertEqual(
            default_expiry(),
            now().date() + datetime.timedelta(days=PERIMETER_DEFAULT_EXPIRY)
        )

    def test_attrs(self):
        # start with the defaults
        at = AccessToken()
        self.assertEqual(at.token, '')
        self.assertEqual(at.is_active, True)
        self.assertEqual(at.expires_on, default_expiry())
        self.assertEqual(at.created_at, None)
        self.assertEqual(at.updated_at, None)
        self.assertEqual(at.created_by, None)

        # check the timestamps
        at = at.save()
        self.assertIsNotNone(at.created_at)
        self.assertEqual(at.updated_at, at.created_at)

        # check the timestamps are updated
        x = at.created_at
        at = at.save()
        # created_at is _not_ updated
        self.assertEqual(at.created_at, x)
        # but updated_at _is_
        self.assertTrue(at.updated_at > at.created_at)

        self.assertTrue(at.is_valid)
        self.assertFalse(at.has_expired)

    def test_cache_key(self):
        token = AccessToken(token="test")
        self.assertIsNotNone(token.cache_key)
        self.assertEqual(token.cache_key, AccessToken.get_cache_key("test"))

    def test_cache_management(self):
        token = AccessToken.objects.create_access_token()
        self.assertEqual(cache.get(token.cache_key), token)
        token.delete()
        self.assertIsNone(cache.get(token.cache_key))

    def test_generate_random_token(self):
        f = AccessToken._meta.get_field('token').max_length
        t1 = AccessToken.random_token_value()
        t2 = AccessToken.random_token_value()
        self.assertNotEqual(t1, t2)
        self.assertEqual(len(t1), f)

    def test_has_expired(self):
        at = AccessToken()
        at.expires_on = YESTERDAY
        self.assertTrue(at.has_expired)
        at.expires_on = TODAY
        self.assertFalse(at.has_expired)
        at.expires_on = TOMORROW
        self.assertFalse(at.has_expired)

    def test_is_valid(self):

        def assertValidity(active, expires, valid):
            return AccessToken(is_active=True, expires_on=TOMORROW).is_valid

        assertValidity(True, YESTERDAY, False)
        assertValidity(True, TODAY, True)
        assertValidity(True, TOMORROW, True)

        assertValidity(False, YESTERDAY, False)
        assertValidity(False, TODAY, False)
        assertValidity(False, TOMORROW, False)

    def test_record(self):
        at = AccessToken(token="test_token").save()
        atu = at.record("hugo@yunojuno.com", "Hugo")
        self.assertEqual(atu, AccessTokenUse.objects.get())
        self.assertEqual(atu.user_email, "hugo@yunojuno.com")
        self.assertEqual(atu.user_name, "Hugo")
        self.assertIsNotNone(atu.timestamp, "Hugo")
        self.assertEqual(atu.client_ip, "unknown")
        self.assertEqual(atu.client_user_agent, "unknown")

class AccesTokenUseTests(TestCase):
    pass
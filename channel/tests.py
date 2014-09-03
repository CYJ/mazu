# -*- cofing: utf-8 -*-
import random

from django.core.urlresolvers import reverse_lazy

from models import Channel
from core.tests import CoreTestCase
from core.tests import random_string


class ChannelTestCase(CoreTestCase):

    def setUp(self):
        super(ChannelTestCase, self).setUp()
        self._random_data()

    def _random_data(self):
        self.channel = {
            'default': True,
            'name': random_string(),
            'host': random_string(),
            'port': random.randint(1024, 65535),
            'ident': random_string(),
            'secret': random_string(),
            'pubchans': random_string(),
            'subchans': random_string(),
            'owner': self.user
        }

    def _create(self):
        Channel(**self.channel).save()

    def test_list_view(self):
        self._create()
        response = self.client.get(reverse_lazy('channel.list'))
        channels = Channel.objects.all()
        for c in response.context['channels']:
            self.assertIn(c, channels)

    def test_display_own_channels(self):
        self._create()
        response = self.client.get(reverse_lazy('channel.list'))
        count = Channel.objects.filter(owner=self.user).count()
        self.assertEqual(count, len(response.context['channels']))

    def test_can_create(self):
        expected_count = Channel.objects.all().count() + 1
        self.client.post(reverse_lazy('channel.create'), self.channel)
        count = Channel.objects.all().count()
        self.assertEqual(count, expected_count)

    def test_can_update(self):
        self._create()
        pk = Channel.objects.get(name=self.channel['name'], owner=self.user).id
        self._random_data()
        self.client.post(reverse_lazy('channel.update', args=[pk]), self.channel)
        updated_channel = Channel.objects.get(id=pk)
        self.assertEqual(updated_channel.name, self.channel['name'])

    def test_can_delete(self):
        self._create()
        expected_count = Channel.objects.all().count() - 1
        pk = Channel.objects.get(name=self.channel['name'], owner=self.user).id
        self.client.post(reverse_lazy('channel.delete', args=[pk]))
        count = Channel.objects.all().count()
        self.assertEqual(count, expected_count)

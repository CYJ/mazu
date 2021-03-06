# -*- coding: utf-8 -*-
from django import forms

from samples.models import Source
from extensions.hpfeeds.models import HPFeedsChannel


class HPFeedsChannelForm(forms.ModelForm):

    """
    Form class used for creating, updating a channel.
    """

    class Meta:
        model = HPFeedsChannel
        fields = [
            'default', 'name', 'host', 'port', 'identity',
            'secret', 'pubchans', 'subchans', 'source'
        ]

    def __init__(self, *args, **kwargs):
        # get current user
        self.user = kwargs.pop('user')
        super(HPFeedsChannelForm, self).__init__(*args, **kwargs)
        # add a filed
        # only offers sources owned by the user
        self.fields['source'] = self.source_field()

    def source_field(self):
        return forms.ModelChoiceField(
            required=False,
            label='Sample Source',
            queryset=Source.objects.filter(user=self.user)
        )

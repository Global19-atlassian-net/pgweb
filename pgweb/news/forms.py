from django import forms
from django.forms import ValidationError

from pgweb.core.models import Organisation
from .models import NewsArticle, NewsTag


class NewsArticleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewsArticleForm, self).__init__(*args, **kwargs)
        self.fields['date'].help_text = 'Use format YYYY-MM-DD'

    def filter_by_user(self, user):
        self.fields['org'].queryset = Organisation.objects.filter(managers=user, approved=True)

    def clean_date(self):
        if self.instance.pk and self.instance.approved:
            if self.cleaned_data['date'] != self.instance.date:
                raise ValidationError("You cannot change the date on an article that has been approved")
        return self.cleaned_data['date']

    @property
    def described_checkboxes(self):
        return {
            'tags': {t.id: t.description for t in NewsTag.objects.all()}
        }

    def clean(self):
        data = super().clean()

        if 'tags' not in data:
            self.add_error('tags', 'Select one or more tags')
        else:
            for t in data['tags']:
                # Check each tag for permissions. This is not very db-efficient, but people
                # don't save news articles that often...
                if t.allowed_orgs.exists() and not t.allowed_orgs.filter(pk=data['org'].pk).exists():
                    self.add_error('tags',
                                   'The organisation {} is not allowed to use the tag {}.'.format(
                                       data['org'],
                                       t,
                                   ))

        return data

    class Meta:
        model = NewsArticle
        exclude = ('submitter', 'approved', 'tweeted')
        widgets = {
            'tags': forms.CheckboxSelectMultiple,
        }

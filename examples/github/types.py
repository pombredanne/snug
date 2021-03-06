import enum
import reprlib
import typing as t
from datetime import datetime
from functools import partial

from dataclasses import dataclass

import snug

_repr = reprlib.Repr()
_repr.maxstring = 45


dclass = partial(dataclass, frozen=True, repr=False)


@dclass()
class UserSummary(snug.utils.StrRepr):
    login:       str
    id:          int
    avatar_url:  str
    gravatar_id: str
    # full:        'User'
    html_url:    str
    type:        str
    site_admin:  bool

    def __str__(self):
        return self.login


@dclass()
class User(UserSummary):
    bio:        str
    blog:       str
    company:    str
    created_at: datetime
    email:      str
    id:         str
    location:   str
    login:      str
    name:       str
    repos_url:  str
    site_admin: str
    updated_at: datetime
    url:        str


@dclass()
class RepoSummary(snug.utils.StrRepr):
    id:          int
    owner:       UserSummary
    name:        str
    full_name:   str
    description: str
    private:     bool
    fork:        bool
    url:         str
    html_url:    str

    def __str__(self):
        return '{} | {}'.format(
            self.name, _repr.repr(self.description))


@dclass()
class Repo(RepoSummary):
    created_at:        datetime
    default_branch:    str
    description:       str
    full_name:         str
    homepage:          str
    id:                int
    language:          str
    name:              str
    open_issues_count: int
    owner:             UserSummary
    private:           bool
    pushed_at:         datetime
    size:              float
    stargazers_count:  int
    updated_at:        datetime
    watchers_count:    int


@dclass()
class Organization(snug.utils.StrRepr):
    """a github organization"""
    blog:        t.Optional[str]
    created_at:  t.Optional[datetime]
    description: t.Optional[str]
    id:          int
    login:       str
    name:        t.Optional[str]
    repos_url:   str
    type:        t.Optional[str]

    def __str__(self):
        try:
            return self.name
        except KeyError:
            return self.login


@dclass()
class Issue(snug.utils.StrRepr):
    """a github issue or pull-request"""

    class State(enum.Enum):
        OPEN = 'open'
        CLOSED = 'closed'
        ALL = 'all'

    number: str
    title: str
    body: str
    state: State

    def __str__(self):
        return f'#{self.number} {self.title}'

    class Sort(enum.Enum):
        CREATED = 'created'
        UPDATED = 'updated'
        COMMENTS = 'comments'

    class Filter(enum.Enum):
        ASSIGNED = 'assigned'
        CREATED = 'created'
        MENTIONED = 'mentioned'
        SUBSCRIBED = 'subscribed'
        ALL = 'all'

import typing as t
from operator import itemgetter

from datetime import datetime

import pytest
from dataclasses import dataclass
from toolz import compose, identity, valmap

from snug import load, utils


@dataclass(frozen=True)
class User:
    """an example dataclass"""
    id:          int
    name:        str
    hobbies:     t.Optional[t.List[str]]
    nicknames:   t.Set[str]
    height:      float
    likes_pizza: t.Optional[bool] = True


@pytest.fixture
def registry():
    return load.PrimitiveRegistry({
        int:        int,
        float:      float,
        bool:       {'true': True, 'false': False}.__getitem__,
        str:        str,
        type(None): identity,
        object:     identity,
        datetime:   utils.parse_iso8601,
    }) | load.GenericRegistry({
        t.List:  load.list_loader,
        t.Set:   load.set_loader,
    }) | load.get_optional_loader


def test_list_loader():
    assert load.list_loader((int, ), [4, '3', '-1']) == [4, 3, -1]


def test_set_loader():
    assert load.set_loader((int, ), [4, '3', '-1']) == {4, 3, -1}


@pytest.mark.parametrize('data, loaded', [
    ({
        'id': 98,
        'username': 'wilma',
        'hobbies': ['tennis', 'diving'],
        'pizza': 'true',
        'height': 1.64,
        'nicknames': []
    },
     User(98, 'wilma', hobbies=['tennis', 'diving'],
          likes_pizza=True, height=1.64, nicknames=set())),
    ({
        'id': '44',
        'username': 'bob',
        'height': '1.85',
        'nicknames': ['bobby'],
    },
     User(44, 'bob', hobbies=None, likes_pizza=None, height=1.85,
          nicknames={'bobby'})
    )
])
def test_create_dataclass_loader(data, loaded, registry):
    dloader = load.create_dataclass_loader(User, registry, valmap(itemgetter, {
        'id':          'id',
        'name':        'username',
        'likes_pizza': 'pizza',
        'height':      'height',
        'nicknames':   'nicknames',
        'hobbies':     'hobbies',
    }))
    assert dloader(data) == loaded


class TestPrimitiveRegistry:

    def test_found(self):
        registry = load.PrimitiveRegistry({int: round})
        loader = registry(int)
        assert loader(3.4) == 3

    def test_not_found(self):
        registry = load.PrimitiveRegistry({int: round})
        with pytest.raises(load.UnsupportedType):
            registry(str)


class TestGenericRegistry:

    def test_ok(self):

        @dataclass(frozen=True)
        class Tag:
            name: str

        registry = load.GenericRegistry({
            t.List: load.list_loader,
        }) | load.PrimitiveRegistry({
            Tag: compose(Tag, '<{}>'.format),
        })

        # simple case
        loader = registry(t.List[Tag])
        assert loader(['hello', 5, 'there']) == [
            Tag('<hello>'), Tag('<5>'), Tag('<there>')
        ]

        # recursive case
        loader = registry(t.List[t.List[Tag]])
        assert loader([
            ['hello', 9, 'there'],
            [],
            ['another', 'list']
        ]) == [
            [Tag('<hello>'), Tag('<9>'), Tag('<there>')],
            [],
            [Tag('<another>'), Tag('<list>')]
        ]

    def test_unsupported_type(self):

        @dataclass(frozen=True)
        class Tag:
            name: str

        registry = load.GenericRegistry({
            t.List: load.list_loader,
        }) | load.PrimitiveRegistry({
            Tag: compose(Tag, '<{}>'.format),
        })
        with pytest.raises(load.UnsupportedType):
            registry(t.Set[Tag])

        with pytest.raises(load.UnsupportedType):
            registry(t.List[str])

        with pytest.raises(load.UnsupportedType):
            registry(object)


class TestGetOptionalLoader:

    def test_ok(self):

        @dataclass(frozen=True)
        class Tag:
            name: str

        registry = load.PrimitiveRegistry({
            Tag: compose(Tag, '<{}>'.format)
        }) | load.get_optional_loader

        loader = registry(t.Optional[Tag])
        assert loader(None) is None
        assert loader(5) == Tag('<5>')


class TestAutoDataclassRegistry:

    def test_ok(self, registry):

        @dataclass
        class Post:
            title: str
            posted_at:  datetime

        registry |= load.AutoDataclassRegistry()
        loader = registry(Post)

        data = {
            'title':     'hello',
            'posted_at': '2017-10-18T14:13:05Z'
        }
        assert loader(data) == Post(
            'hello',
            datetime(2017, 10, 18, 14, 13, 5))

    def test_not_supported(self, registry):

        class MyClass():
            pass

        registry |= load.AutoDataclassRegistry()

        with pytest.raises(load.UnsupportedType):
            registry(MyClass)


def test_dataclass_registry(registry):

    @dataclass
    class Post:
        title:     str
        posted_at: datetime
        author_id: int

    data = {
        'Title':     'hello',
        'date':      '2017-10-18T14:13:05Z',
        'author_id': 12,
    }

    registry |= load.DataclassRegistry({
        Post: {
            'title':     itemgetter('Title'),
            'posted_at': itemgetter('date'),
            'author_id': itemgetter('author_id'),
        }
    })

    loader = registry(Post)

    assert loader(data) == Post(
        'hello',
        datetime(2017, 10, 18, 14, 13, 5),
        author_id=12)

    with pytest.raises(load.UnsupportedType):
        registry(User)


def test_simple_registry():

    @dataclass
    class User:
        name:     str
        id:       int
        nickname: t.Optional[str]

    @dataclass
    class Post:
        title:     str
        user:      User
        comments:  t.List[str]

    loader = load.simple_registry(Post)

    loaded = loader({
        'title': 'hello',
        'comments': ['first!', 'another comment', 5],
        'user': {
            'name': 'bob',
            'id': '543',
            'extra data': '...',
        }
    })
    assert loaded == Post(
        title='hello',
        comments=['first!', 'another comment', '5'],
        user=User(
            name='bob',
            id=543,
            nickname=None
        )
    )

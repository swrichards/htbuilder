# Copyright 2020 Thiago Teixeira
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
htbuilder -- Tiny HTML string builder for Python
===========================================

Build HTML strings using a purely functional syntax:

Example
-------

If using Python 3.7+:

>>> from htbuilder import div, ul, li, img  # This syntax requires Python 3.7+
>>>
>>> image_paths = [
...   "http://...",
...   "http://...",
...   "http://...",
... ]
>>>
>>> out = div(id="container")(
...   ul(_class="image-list")(
...     [
...       li(img(src=image_path, _class="large-image"))
...       for image_path in image_paths
...     ]
...   )
... )
>>>
>>> print(out)
>>>
>>> # Or convert to string with:
>>> x = str(out)


If using Python < 3.7, the import should look like this instead:

>>> from htbuilder import H
>>>
>>> div = H.div
>>> ul = H.ul
>>> li = H.li
>>> img = H.img
>>>
>>> # ...then the rest is the same as in the previous example.

"""

from more_itertools import collapse

from .funcs import func
from .units import unit
from .utils import classes, fonts, rule, styles

EMPTY_ELEMENTS = set(
    [
        # https://developer.mozilla.org/en-US/docs/Glossary/Empty_element
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "keygen",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
        # SVG
        "circle",
        "line",
        "path",
        "polygon",
        "polyline",
        "rect",
    ]
)


class _ElementCreator(object):
    def __getattr__(self, tag):
        return HtmlTag(tag)


class HtmlTag(object):
    def __init__(self, tag):
        """HTML element builder."""
        self._tag = tag

    def __call__(self, *args, **kwargs):
        if args and kwargs:
            raise ValueError("Accept args or kwargs in element, but not both.")

        return HtmlElement(self._tag)(*args, **kwargs)



VOIDED_CHILDREN = (None, False, True)


class HtmlElement(object):
    def __init__(self, tag, attrs={}, children=[]):
        """An HTML element."""
        self._tag = tag.lower()
        self._attrs = attrs
        self._children = children
        self._is_empty = tag in EMPTY_ELEMENTS

    def __call__(self, *children, **attrs):
        if children:
            if self._is_empty:
                raise TypeError("<%s> cannot have children" % self._tag)
            self._children = list(collapse([*self._children, *children]))

        if attrs:
            self._attrs = {**self._attrs, **attrs}

        return self

    def __getattr__(self, name):
        if name in self._attrs:
            return self._attrs[name]
        raise AttributeError("No such attribute %s" % name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        self._attrs[name] = value

    def __delattr__(self, name):
        del self._attrs[name]

    def __str__(self):
        html = self._get_html_template() % {
            "tag": _clean_name(self._tag),
            "attrs": _serialize_attrs(self._attrs),
            "children": _render_children(self._children),
        }

        if self._tag == "html":
            return "<!DOCTYPE html>%(html)s" % {"html": html}

        return html

    def _get_html_template(self) -> str:
        if self._is_empty:
            return "<%(tag)s %(attrs)s/>" if self._attrs else "<%(tag)s/>"

        return (
            "<%(tag)s %(attrs)s>%(children)s</%(tag)s>"
            if self._attrs
            else "<%(tag)s>%(children)s</%(tag)s>"
        )


def _render_children(children):
    return "".join(
        [str(c) for c in children if all(c is not uc for uc in VOIDED_CHILDREN)]
    )


def _serialize_attrs(attrs):
    """Serialize HTML attributes to a string."""
    return " ".join(
        [
            f'{_clean_name(k)}="{v}"' if v is not True else _clean_name(k)
            for k, v in attrs.items()
            if (v is not None and v is not False)
        ]
    )


def _clean_name(k: str) -> str:
    # This allows you to use reserved words by appending an underscore as a suffix.
    # For example, use "class_" instead of "class". If an underscore prefix is provided,
    # a ValueError exception will be raised.
    if k.startswith("_"):
        raise ValueError(
            "Underscore prefix for reserved words not supported, use suffix instead."
        )

    return k.rstrip("_").replace("_", "-")


def fragment(*args):
    return _render_children(args)


# Python >= 3.7
# https://docs.python.org/3/reference/datamodel.html#customizing-module-attribute-access
def __getattr__(tag):
    return HtmlTag(tag)


# For Python < 3.7
H = _ElementCreator()

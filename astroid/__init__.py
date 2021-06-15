# Copyright (c) 2006-2013, 2015 LOGILAB S.A. (Paris, FRANCE) <contact@logilab.fr>
# Copyright (c) 2014 Google, Inc.
# Copyright (c) 2014 Eevee (Alex Munroe) <amunroe@yelp.com>
# Copyright (c) 2015-2016, 2018, 2020 Claudiu Popa <pcmanticore@gmail.com>
# Copyright (c) 2015-2016 Ceridwen <ceridwenv@gmail.com>
# Copyright (c) 2016 Derek Gustafson <degustaf@gmail.com>
# Copyright (c) 2016 Moises Lopez <moylop260@vauxoo.com>
# Copyright (c) 2018 Bryce Guinta <bryce.paul.guinta@gmail.com>
# Copyright (c) 2019 Nick Drozd <nicholasdrozd@gmail.com>
# Copyright (c) 2020-2021 hippo91 <guillaume.peillex@gmail.com>
# Copyright (c) 2021 Pierre Sassoulas <pierre.sassoulas@gmail.com>
# Copyright (c) 2021 Marc Mueller <30130371+cdce8p@users.noreply.github.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/LICENSE

"""Python Abstract Syntax Tree New Generation

The aim of this module is to provide a common base representation of
python source code for projects such as pychecker, pyreverse,
pylint... Well, actually the development of this library is essentially
governed by pylint's needs.

It extends class defined in the python's _ast module with some
additional methods and attributes. Instance attributes are added by a
builder object, which can either generate extended ast (let's call
them astroid ;) by visiting an existent ast tree or by inspecting living
object. Methods are added by monkey patching ast classes.

Main modules are:

* nodes and scoped_nodes for more information about methods and
  attributes added to different node classes

* the manager contains a high level object to get astroid trees from
  source files and living objects. It maintains a cache of previously
  constructed tree for quick access

* builder contains the class responsible to build astroid trees
"""

import enum

import os
from importlib import import_module
from pathlib import Path


from .__pkginfo__ import __version__, version

_Context = enum.Enum("Context", "Load Store Del")
Load = _Context.Load
Store = _Context.Store
Del = _Context.Del
del _Context


# WARNING: internal imports order matters !
# pylint: disable=wrong-import-order,wrong-import-position,redefined-builtin

# make all exception classes accessible from astroid package
from astroid.exceptions import (
    AstroidBuildingError,
    AstroidBuildingException,
    AstroidError,
    AstroidImportError,
    AstroidIndexError,
    AstroidSyntaxError,
    AstroidTypeError,
    AstroidValueError,
    AttributeInferenceError,
    BinaryOperationError,
    DuplicateBasesError,
    InconsistentMroError,
    InferenceError,
    InferenceOverwriteError,
    MroError,
    NameInferenceError,
    NoDefault,
    NotFoundError,
    OperationError,
    ResolveError,
    SuperArgumentTypeError,
    SuperError,
    TooManyLevelsError,
    UnaryOperationError,
    UnresolvableName,
    UseInferenceDefault,
)

# make all node classes accessible from astroid package
from astroid.nodes import *

# trigger extra monkey-patching
from astroid import inference

# more stuff available
from astroid import raw_building
from astroid.inference_tip import _inference_tip_cached, inference_tip
from astroid.bases import BaseInstance, Instance, BoundMethod, UnboundMethod
from astroid.node_classes import are_exclusive, unpack_infer
from astroid.scoped_nodes import builtin_lookup
from astroid.builder import parse, extract_node
from astroid.util import Uninferable

# make a manager instance (borg) accessible from astroid package
from astroid.manager import AstroidManager

MANAGER = AstroidManager()
del AstroidManager


def register_module_extender(manager, module_name, get_extension_mod):
    def transform(node):
        extension_module = get_extension_mod()
        for name, objs in extension_module.locals.items():
            node.locals[name] = objs
            for obj in objs:
                if obj.parent is extension_module:
                    obj.parent = node

    manager.register_transform(Module, transform, lambda n: n.name == module_name)


# load brain plugins
BRAIN_MODULES_DIR = Path(__file__).with_name("brain")
for module in os.listdir(BRAIN_MODULES_DIR):
    if module.endswith(".py"):
        import_module(f"astroid.brain.{module[:-3]}")

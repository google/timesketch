# Copyright 2017, Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools


def get_prop_name_from_method(method):
    name = method.__name__
    if name.startswith('get_'):
        return name[4:]
    elif name.startswith('is_'):
        return name[3:]
    elif name.startswith('has_'):
        return name[4:]
    else:
        raise TypeError(
            'PyCypher getter method has to start with one of'
            ' "get_", "is_" or "has_".'
        )


def pycypher_getter(method):
    name = get_prop_name_from_method(method)
    @functools.wraps(method)
    def wrapper(self):
        if name in self._props:
            return self._props[name]
        if name in self._indirect_props:
            children = self._all_descendants()
        else:
            children = self._children
        children = [child for child in children if child.role == name]
        if not children:
            return None
        elif len(children) == 1:
            return children[0]
        else:
            raise ValueError(
                'Multiple children with singleton role "%s".' % name
            )
    return wrapper


def pycypher_list_getter(role):
    def inner(method):
        name = get_prop_name_from_method(method)
        @functools.wraps(method)
        def wrapper(self):
            if name in self._props:
                return self._props[name]
            if role in self._indirect_props:
                children = self._all_descendants()
            else:
                children = self._children
            return [child for child in children if child.role == role]
        return wrapper
    return inner


class GettersMixin(object):
    @pycypher_getter
    def get_accumulator(self):
        pass

    @pycypher_list_getter('action')
    def get_actions(self):
        pass

    @pycypher_getter
    def get_alias(self):
        pass

    @pycypher_getter
    def get_argument(self):
        pass

    @pycypher_getter
    def get_argument1(self):
        pass

    @pycypher_getter
    def get_argument2(self):
        pass

    @pycypher_list_getter('argument')
    def get_arguments(self):
        pass

    @pycypher_getter
    def get_body(self):
        pass

    @pycypher_list_getter('clause')
    def get_clauses(self):
        pass

    @pycypher_getter
    def get_default(self):
        pass

    @pycypher_getter
    def get_direction(self):
        pass

    @pycypher_getter
    def get_distinct(self):
        pass

    @pycypher_list_getter('element')
    def get_elements(self):
        pass

    @pycypher_getter
    def get_end(self):
        pass

    @pycypher_getter
    def get_eval(self):
        pass

    @pycypher_getter
    def get_expression(self):
        pass

    @pycypher_list_getter('expression')
    def get_expressions(self):
        pass

    @pycypher_getter
    def get_field_terminator(self):
        pass

    @pycypher_getter
    def get_func_name(self):
        pass

    @pycypher_list_getter('hint')
    def get_hints(self):
        pass

    @pycypher_getter
    def get_identifier(self):
        pass

    @pycypher_list_getter('identifier')
    def get_identifiers(self):
        pass

    @pycypher_list_getter('id')
    def get_ids(self):
        pass

    @pycypher_getter
    def get_index_name(self):
        pass

    @pycypher_getter
    def get_init(self):
        pass

    @pycypher_list_getter('item')
    def get_items(self):
        pass

    @pycypher_list_getter('key')
    def get_keys(self):
        pass

    @pycypher_getter
    def get_label(self):
        pass

    @pycypher_list_getter('label')
    def get_labels(self):
        pass

    @pycypher_getter
    def get_limit(self):
        pass

    @pycypher_getter
    def get_lookup(self):
        pass

    @pycypher_getter
    def get_name(self):
        pass

    @pycypher_getter
    def get_operator(self):
        pass

    @pycypher_list_getter('operator')
    def get_operators(self):
        pass

    @pycypher_list_getter('option')
    def get_options(self):
        pass

    @pycypher_getter
    def get_order_by(self):
        pass

    @pycypher_list_getter('param')
    def get_params(self):
        pass

    @pycypher_getter
    def get_path(self):
        pass

    @pycypher_list_getter('path')
    def get_paths(self):
        pass

    @pycypher_getter
    def get_pattern(self):
        pass

    @pycypher_getter
    def get_pattern_path(self):
        pass

    @pycypher_list_getter('point')
    def get_points(self):
        pass

    @pycypher_getter
    def get_predicate(self):
        pass

    @pycypher_list_getter('predicate')
    def get_predicates(self):
        pass

    @pycypher_getter
    def get_proc_name(self):
        pass

    @pycypher_list_getter('projection')
    def get_projections(self):
        pass

    @pycypher_getter
    def get_properties(self):
        pass

    @pycypher_getter
    def get_property(self):
        pass

    @pycypher_getter
    def get_prop_name(self):
        pass

    @pycypher_getter
    def get_query(self):
        pass

    @pycypher_getter
    def get_reltype(self):
        pass

    @pycypher_list_getter('reltype')
    def get_reltypes(self):
        pass

    @pycypher_list_getter('selector')
    def get_selectors(self):
        pass

    @pycypher_getter
    def get_skip(self):
        pass

    @pycypher_getter
    def get_start(self):
        pass

    @pycypher_getter
    def get_subscript(self):
        pass

    @pycypher_getter
    def get_url(self):
        pass

    @pycypher_getter
    def get_value(self):
        pass

    @pycypher_list_getter('value')
    def get_values(self):
        pass

    @pycypher_getter
    def get_valuestr(self):
        pass

    @pycypher_getter
    def get_varlength(self):
        pass

    @pycypher_getter
    def get_version(self):
        pass

    @pycypher_getter
    def is_distinct(self):
        pass

    @pycypher_getter
    def is_optional(self):
        pass

    @pycypher_getter
    def is_unique(self):
        pass

    @pycypher_getter
    def is_ascending(self):
        pass

    @pycypher_getter
    def is_single(self):
        pass

    @pycypher_getter
    def has_detach(self):
        pass

    @pycypher_getter
    def has_include_existing(self):
        pass

    @pycypher_getter
    def has_all(self):
        pass

    @pycypher_getter
    def has_with_headers(self):
        pass

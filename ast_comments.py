import ast
import sys
import tokenize
from ast import *  # noqa: F401,F403
from collections.abc import Iterable
from typing import Dict, List, Tuple, Union


class Comment(ast.AST):
    value: str
    _fields = ("value",)


_CONTAINER_ATTRS = ["body", "handlers", "orelse", "finalbody"]


def parse(source: Union[str, bytes, ast.AST], *args, **kwargs) -> ast.AST:
    tree = ast.parse(source, *args, **kwargs)
    if isinstance(source, (str, bytes)):
        _enrich(source, tree)
    return tree


def _enrich(source: Union[str, bytes], tree: ast.AST) -> None:
    if isinstance(source, bytes):
        source = source.decode()
    lines_iter = iter(source.splitlines(keepends=True))
    tokens = tokenize.generate_tokens(lambda: next(lines_iter))

    comment_nodes = []
    for t in tokens:
        if t.type != tokenize.COMMENT:
            continue
        lineno, col_offset = t.start
        end_lineno, end_col_offset = t.end
        c = Comment(
            value=t.string,
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
        )
        comment_nodes.append(c)

    if not comment_nodes:
        return

    tree_intervals = _get_tree_intervals(tree)
    for c_node in comment_nodes:
        c_lineno = c_node.lineno
        possible_intervals_for_c_node = [
            (x, y) for x, y in tree_intervals if x <= c_lineno <= y
        ]

        if possible_intervals_for_c_node:
            target_interval = tree_intervals[max(possible_intervals_for_c_node)]

            target_node = target_interval["node"]
            # intervals for every attribute from _CONTAINER_ATTRS for the target node
            sub_intervals = target_interval["intervals"]

            loc = -1
            for i, (low, high, _) in enumerate(sub_intervals):
                if low <= c_lineno <= high or c_lineno < low:
                    loc = i
                    break

            *_, target_attr = sub_intervals[loc]
        else:
            target_node = tree
            target_attr = "body"

        attr = getattr(target_node, target_attr)
        attr.append(c_node)
        attr.sort(key=lambda x: (x.end_lineno, not isinstance(x, Comment)))


def _get_tree_intervals(
    node: ast.AST,
) -> Dict[Tuple[int, int], Dict[str, Union[List[Tuple[int, int]], ast.AST]]]:
    res = {}
    for node in ast.walk(node):
        attr_intervals = []
        for attr in _CONTAINER_ATTRS:
            if items := getattr(node, attr, None):
                if not isinstance(items, Iterable):
                    continue
                attr_intervals.append((*_get_interval(items), attr))
        if attr_intervals:
            low = node.lineno if hasattr(node, "lineno") else min(attr_intervals)[0]
            high = (
                node.end_lineno
                if hasattr(node, "endlineno")
                else max(attr_intervals)[1]
            )
            res[(low, high)] = {"intervals": attr_intervals, "node": node}
    return res


def _get_interval(items: List[ast.AST]) -> Tuple[int, int]:
    linenos, end_linenos = [], []
    for item in items:
        linenos.append(item.lineno)
        end_linenos.append(item.end_lineno)
    return min(linenos), max(end_linenos)


# `unparse` has been introduced in Python 3.9
if sys.version_info >= (3, 9):

    class _Unparser(ast._Unparser):
        def visit_Comment(self, node: "Comment"):
            self.fill(node.value)

    def unparse(ast_obj):
        return _Unparser().visit(ast_obj)

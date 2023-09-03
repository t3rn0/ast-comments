import ast
import sys
import tokenize
from ast import *  # noqa: F401,F403
from collections.abc import Iterable
from typing import Dict, List, Tuple, Union


class Comment(ast.AST):
    value: str
    inline: bool
    _fields = (
        "value",
        "inline",
    )


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
            inline=t.string != t.line.strip("\n").strip(" "),
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
        )
        comment_nodes.append(c)

    if not comment_nodes:
        return

    tree_intervals = _get_tree_intervals(source, tree)
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
        attr.sort(key=lambda x: (x.end_lineno, isinstance(x, Comment)))

        # NOTE:
        # Due to some issues it's possible for comment nodes to go outside of their initial place
        # after the parse-unparse roundtip:
        #   before parse/unparse:
        #   ```
        #   # comment 0
        #   some_code  # comment 1
        #   ```
        #   after parse/unparse:
        #   ```
        #   # comment 0  # comment 1
        #   some_code
        #   ```
        # As temporary workaround I decided to correct inline attributes here so they don't
        # overlap with each other. This place should be revisited after solving following issues:
        # - https://github.com/t3rn0/ast-comments/issues/10
        # - https://github.com/t3rn0/ast-comments/issues/13
        for left, right in zip(attr[:-1], attr[1:]):
            if isinstance(left, Comment) and isinstance(right, Comment):
                right.inline = False
    target_node.end_lineno = c_node.end_lineno
    target_node.end_col_offset = c_node.end_col_offset

def _get_tree_intervals(
    source: str,
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
                if hasattr(node, "end_lineno")
                else max(attr_intervals)[1]
            )
            # Add trailing comment lines, doesn't match indentation
            for line in source.splitlines()[high:]:
                if line.strip().startswith("#"):
                    high += 1
                else:
                    break
            res[(low, high)] = {"intervals": attr_intervals, "node": node}
    return res


# get min and max line from a source tree
def _get_interval(items: List[ast.AST]) -> Tuple[int, int]:
    linenos, end_linenos = [], []
    for item in items:
        linenos.append(item.lineno)
        end_linenos.append(item.end_lineno)
    return min(linenos), max(end_linenos)


# `unparse` has been introduced in Python 3.9
if sys.version_info >= (3, 9):

    class _Unparser(ast._Unparser):
        def visit_Comment(self, node: Comment) -> None:
            if node.inline:
                self.write(f"  {node.value}")
            else:
                self.fill(node.value)

        def visit_If(self, node: ast.If) -> None:
            def _get_first_not_comment_idx(orelse: list[ast.stmt]) -> int:
                i = 0
                while i < len(orelse) and isinstance(orelse[i], Comment):
                    i += 1
                return i

            self.fill("if ")
            self.traverse(node.test)
            with self.block():
                self.traverse(node.body)
            # collapse nested ifs into equivalent elifs.
            while node.orelse:
                i = _get_first_not_comment_idx(node.orelse)
                if len(node.orelse[i:]) != 1 or not isinstance(node.orelse[i], ast.If):
                    break
                for c_node in node.orelse[:i]:
                    self.traverse(c_node)
                node = node.orelse[i]
                self.fill("elif ")
                self.traverse(node.test)
                with self.block():
                    self.traverse(node.body)
            # final else
            if node.orelse:
                self.fill("else")
                with self.block():
                    self.traverse(node.orelse)

    def unparse(ast_obj: ast.AST) -> str:
        return _Unparser().visit(ast_obj)


def get_source_segment(source, node, *, padded=False):
    """Get source code segment of the *source* that generated *node*.

    If some location information (`lineno`, `end_lineno`, `col_offset`,
    or `end_col_offset`) is missing, return None.

    If *padded* is `True`, the first line of a multi-line statement will
    be padded with spaces to match its original position.

    Customized version of ast.get_source_segment that includes trailing
    inline comments.
    """
    try:
        if node.end_lineno is None or node.end_col_offset is None:
            return None
        lineno = node.lineno - 1
        end_lineno = node.end_lineno - 1
        col_offset = node.col_offset
        # Add trailing inline comment:
        end_col_offset = max(node.body[-1].end_col_offset, node.end_col_offset)
    except AttributeError:
        return None

    lines = ast._splitlines_no_ff(source)
    if end_lineno == lineno:
        return lines[lineno].encode()[col_offset:end_col_offset].decode()

    if padded:
        padding = ast._pad_whitespace(lines[lineno].encode()[:col_offset].decode())
    else:
        padding = ''

    first = padding + lines[lineno].encode()[col_offset:].decode()
    last = lines[end_lineno].encode()[:end_col_offset].decode()
    lines = lines[lineno+1:end_lineno]

    lines.insert(0, first)
    lines.append(last)
    return ''.join(lines)

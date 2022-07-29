import ast
import tokenize
from ast import *
from typing import List, Protocol, Tuple, Union


class stmt(ast.stmt):
    comments: Tuple[str, ...]


class AstNode(Protocol):
    body: List[stmt]


def format_comment(comment_string: str):
    return comment_string.lstrip("# ")


def parse(source: Union[str, bytes, AstNode], *args, **kwargs) -> AstNode:
    if isinstance(source, AstNode):
        return source
    tree = ast.parse(source, *args, **kwargs)
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt):
            node._fields += ("comments",)
            node.comments = ()  # type: ignore
    _enrich(source, tree)
    return tree


def _enrich(source: Union[str, bytes], tree: AstNode) -> None:
    if isinstance(source, bytes):
        source = source.decode()
    lines_iter = iter(source.splitlines(keepends=True))
    tokens = tokenize.generate_tokens(lambda: next(lines_iter))

    comment_tokens = sorted(
        (x.start[0], x) for x in tokens if x.type == tokenize.COMMENT
    )
    nodes = sorted([(x.lineno, x) for x in ast.walk(tree) if isinstance(x, ast.stmt)])  # type: ignore

    i = j = 0
    while i < len(comment_tokens) and j < len(nodes):
        t_lineno, token = comment_tokens[i]
        n_lineno, node = nodes[j]
        if t_lineno <= n_lineno:
            node.comments += (format_comment(token.string),)  # type: ignore
            i += 1
        else:
            j += 1

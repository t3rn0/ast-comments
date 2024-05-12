import ast
import re
import sys
import tokenize
import typing as _t
from ast import *  # noqa: F401,F403
from collections.abc import Iterable
from dataclasses import dataclass

import logging

logger = logging.getLogger(__name__)

class Comment(ast.AST):
    if sys.version_info >= (3, 10):
        __match_args__ = ("value", "inline")
    _attributes = ("lineno", "col_offset", "end_lineno", "end_col_offset")
    value: str
    inline: bool
    _fields = (
        "value",
        "inline",
    )

    def __repr__(self):
        return f"{self.__class__.__name__}(value={self.value}, inline={self.inline})"

@dataclass
class BlockWithRange:
    block: list[ast.AST]
    lineno: int
    end_lineno: int

def parse(source: _t.Union[str, bytes, ast.AST], *args, **kwargs) -> ast.AST:
    tree = ast.parse(source, *args, **kwargs)
    if isinstance(source, (str, bytes)):
        if isinstance(source, bytes):
            source = source.decode()
        ASTEnrichmentWithComments(source, tree).enrich()
    return tree

class ASTEnrichmentWithComments:
    _CONTAINER_ATTRS = ["body", "handlers", "orelse", "finalbody", "elts", "keys"]
    _KEYWORDS = ["if", "else", "elif", "try", "except", "finally", "while", "for"]

    def __init__(self, source: str, tree: ast.AST):
        self.source = source
        lines = source.split("\n")
        # Insert an empty line to correspond to the lineno values from ast nodes which start at 1
        # instead of 0
        lines.insert(0, "")
        self.lines = lines
        self.tree = tree
    
    @staticmethod
    def extract_comment_nodes(code: str):
        lines_iter = iter(code.splitlines(keepends=True))
        tokens = tokenize.generate_tokens(lambda: next(lines_iter))

        comment_nodes = []
        for t in tokens:
            if t.type != tokenize.COMMENT:
                continue
            lineno, col_offset = t.start
            end_lineno, end_col_offset = t.end
            c = Comment(
                value=t.string,
                inline=t.string != t.line.strip("\n").lstrip(" "),
                lineno=lineno,
                col_offset=col_offset,
                end_lineno=end_lineno,
                end_col_offset=end_col_offset,
            )
            comment_nodes.append(c)
        return comment_nodes

    def enrich(self):
        comment_nodes = ASTEnrichmentWithComments.extract_comment_nodes(self.source)

        if not comment_nodes:
            return

        self.append_comment_nodes(self.tree, comment_nodes)
    
    def append_comment_nodes(self, tree, comment_nodes: list[Comment]):
        comment_nodes_set = set(comment_nodes)
        
        for node in ast.walk(tree):
            if isinstance(node, Comment):
                continue
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                node_lines_count = node.end_lineno - node.lineno + 1
                comments_inside_node = self.comments_in_lines_range(comment_nodes_set, node.lineno, node.end_lineno)
                comments_inside_children = set()
                block_ranges: list[BlockWithRange] = []
                children = []
                for attr_name in dir(node):
                    attr = getattr(node, attr_name)
                    if attr_name in ASTEnrichmentWithComments._CONTAINER_ATTRS:
                        block = attr
                        if isinstance(block, list) and len(block) > 0:
                            # fill node blocks
                            low, high = self.get_block_range(block)
                            block_ranges.append(BlockWithRange(block, low, high))
                    elif attr_name == "comment":
                        pass
                    elif node_lines_count > 1:
                        # child on any line expect the node's last one can have comment inside
                        if isinstance(attr, ast.AST) and not isinstance(attr, Comment):
                            child_node = attr
                            self.append_child_with_inner_comment(node, comment_nodes_set, child_node, children, comments_inside_children)
                        elif isinstance(attr, list):
                            children_nodes = attr
                            for child_node in children_nodes:
                                if isinstance(child_node, ast.AST) and not isinstance(child_node, Comment):
                                    self.append_child_with_inner_comment(node, comment_nodes_set, child_node, children, comments_inside_children)                                    

                block_ranges.sort(key=lambda b: b.lineno)
                node_comments = comments_inside_node - comments_inside_children
                for node_comment in node_comments:
                    if node_comment.inline:
                        # process inline or control expression oneline comment
                        if len(children) > 0:
                            inf_child = self.get_inf_node_for_comment(children, node_comment)
                            if inf_child is not None:
                                inf_child.comment = node_comment
                                self.add_comment_field_to_node_class(inf_child)
                                comment_nodes_set.remove(node_comment)
                                continue
                        if len(block_ranges) > 0:
                            # comment after "if", "else", "try", "finally" and etc. Add it as not inline before the first block
                            sup_block = self.get_sup_block_for_comment(block_ranges, node_comment)
                            if sup_block is not None:
                                node_comment.inline = False
                                self.add_comment_to_block(sup_block.block, node_comment)
                                comment_nodes_set.remove(node_comment)
                                continue
                        else:
                            node.comment = node_comment
                            self.add_comment_field_to_node_class(node)
                            comment_nodes_set.remove(node_comment)
                            continue
                    else:
                        # add online comment intp appropriate block
                        if len(block_ranges) > 0:
                            block_or_inside_child = self.get_block_around_comment(block_ranges, node_comment)
                            if block_or_inside_child == False:
                                continue
                            block = block_or_inside_child
                            if block is None:
                                inf_block = self.get_inf_block_for_comment(block_ranges, node_comment)
                                sup_block = self.get_sup_block_for_comment(block_ranges, node_comment)
                                block = None
                                if inf_block is not None and sup_block is not None:
                                    for line_number in range(sup_block.lineno, inf_block.end_lineno, -1):
                                        line = self.lines[line_number]
                                        if not self.is_comment_line(line):
                                            for keyword in ASTEnrichmentWithComments._KEYWORDS:
                                                if keyword in line: # TODO: check more strong node type
                                                    block = inf_block if node_comment.lineno < line_number else sup_block
                                                    break
                                        if block is not None:
                                            break
                                    
                                else:
                                    block = inf_block or sup_block
                            if block is not None:
                                self.add_comment_to_block(block.block, node_comment)
                                comment_nodes_set.remove(node_comment)
                                continue
        
        for comment_node in comment_nodes_set:
            body = getattr(self.tree, "body")
            self.add_comment_to_block(body, comment_node)


    def append_child_with_inner_comment(self, node, comment_nodes_set, child_node, children, comments_inside_children: set):
        if hasattr(child_node, "lineno") and hasattr(child_node, "end_lineno"):
            child_comment_last_line = min(child_node.end_lineno, node.end_lineno - 1)
            if child_comment_last_line >= child_node.lineno:
                children.append(child_node)
                comments_inside_child_node = self.comments_in_lines_range(comment_nodes_set, child_node.lineno, child_comment_last_line)
                comments_inside_children.update(comments_inside_child_node)        

    def get_inf_node_for_comment(self, nodes: list[ast.AST], node_comment: Comment):
        inf_node = None
        for node in nodes:
            if node.lineno <= node_comment.lineno <= node.end_lineno and (inf_node is None or inf_node.end_col_offset < node.end_col_offset):
                inf_node = node
        return inf_node

    def get_block_around_comment(self, blocks: list[BlockWithRange], node_comment: Comment):
        for block in blocks:
            if block.lineno <= node_comment.lineno and node_comment.end_lineno <= block.end_lineno:
                for block_node in block.block:
                    if block_node.lineno <= node_comment.lineno and node_comment.end_lineno <= block_node.end_lineno:
                        return False
                return block
        return None

    def get_inf_block_for_comment(self, blocks: list[BlockWithRange], node_comment: Comment):
        inf_block = None
        for block in blocks:
            if block.end_lineno < node_comment.lineno and (inf_block is None or inf_block.end_lineno < block.end_lineno):
                inf_block = block
        return inf_block
    
    def get_sup_block_for_comment(self, blocks: list[BlockWithRange], node_comment: Comment):
        sup_block = None
        for block in blocks:
            if block.lineno > node_comment.end_lineno and (sup_block is None or sup_block.lineno > block.lineno):
                sup_block = block
        return sup_block

    def comments_in_lines_range(self, comment_nodes: list[Comment], low: int, high: int):
        return set([comment_node for comment_node in comment_nodes if low <= comment_node.lineno <= high])

    def get_block_range(self, block: list[ast.AST]):
        linenos, end_linenos = [], []
        for node in block:
            linenos.append(node.lineno)
            end_linenos.append(node.end_lineno)
        return min(linenos), max(end_linenos)
    
    def add_comment_to_block(self, block, comment_node):
        block.append(comment_node)
        block.sort(key=lambda x: (x.end_lineno, isinstance(x, Comment)))

    def is_comment_line(self, line: str):
        return re.match(r"^ *#.*", line) is not None

    def add_comment_field_to_node_class(self, node: ast.AST):
        fields = set(node.__class__._fields)
        field_name = "comment"
        if field_name not in fields:
            fields.add("comment")
            node.__class__._fields = tuple(fields)


def unparse(ast_obj: ast.AST) -> str:
    return _Unparser().visit(ast_obj)


def pre_compile_fixer(tree: ast.AST) -> ast.AST:
    """
    The parse output from ast_comments cannot compile (see issue #23). This function can be
    run to fix the output so that it can compile.  This transformer strips out Comment nodes.
    """

    class RewriteComments(ast.NodeTransformer):
        def visit_Comment(self, node: ast.AST) -> ast.AST:
            return None

    return RewriteComments().visit(tree)


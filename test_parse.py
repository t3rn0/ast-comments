"""Tests for `ast_comments.parse`."""

import ast
from textwrap import dedent

import pytest

from ast_comments import Comment, parse


def test_comment_at_start_of_inner_block_getting_correctly_parsed():
    """Comment at the start of a new inlined block/interval"""
    source = dedent(
        """
        def test():
            # Comment at start of block
            hello = 'hello'
        """
    )
    nodes = parse(source).body
    assert isinstance(nodes[0].body[0], Comment)


def test_comment_at_start_of_inner_block_with_wrong_indentation_is_still_inside_the_block():
    """Comment at the start of a new inlined block/interval with wrong indentation"""
    source = dedent(
        """
        def test():
        # Comment at start of block
            hello = 'hello'
        """
    )
    nodes = parse(source).body
    assert isinstance(nodes[0].body[0], Comment)


def test_comment_at_end_of_inner_block_getting_correctly_parsed():
    """Comment at the end of a new inlined block/interval"""
    source = dedent(
        """
        def test():
            hello = 'hello'
            # Comment at end of block
        """
    )
    nodes = parse(source).body
    assert isinstance(nodes[0].body[1], Comment)


def test_comment_at_end_of_inner_block_with_wrong_indentation_gets_moved_to_next_block():
    """Comment at the end of a new inlined block/interval with wrong indentation should get assigned to next block"""
    source = dedent(
        """
        if 1 == 1:
            hello = 'hello'
        # Comment at end of block
        else:
            hello = 'hello'
        """
    )
    nodes = parse(source).body
    assert isinstance(nodes[0].orelse[0], Comment)


def test_single_comment_in_tree():
    """Parsed tree has Comment node."""
    source = """# comment"""
    nodes = parse(source).body
    assert len(nodes) == 1
    assert isinstance(nodes[0], Comment)
    assert not nodes[0].inline


def test_comment_ends_with_space():
    """Spaces at the end of a comment does not change its inlined value."""
    source = """# comment """
    nodes = parse(source).body
    assert not nodes[0].inline


def test_separate_line_single_line():
    """Comment to the following line. Order in which nodes appears is preserved."""
    source = dedent(
        """
        # comment to hello
        hello = 'hello'
        """
    )
    nodes = parse(source).body
    assert len(nodes) == 2
    assert isinstance(nodes[0], Comment)
    assert not nodes[0].inline


def test_inline_comment_after_statement():
    """Inlined comment goes after statement."""
    source = """hello = 'hello' # comment to hello"""
    nodes = parse(source).body
    assert len(nodes) == 2
    assert isinstance(nodes[1], Comment)
    assert nodes[1].inline


def test_separate_line_multiline():
    """Multiple comments to the following line."""
    source = dedent(
        """
        # comment to hello 1
        # comment to hello 2
        hello = 'hello'
        """
    )
    nodes = parse(source).body
    assert len(nodes) == 3
    assert isinstance(nodes[0], Comment)
    assert isinstance(nodes[1], Comment)
    assert nodes[0].value == "# comment to hello 1"
    assert nodes[1].value == "# comment to hello 2"
    assert not nodes[0].inline
    assert not nodes[1].inline


def test_multiline_and_inline_combined():
    """Multiple comments to the following line combined with inline comment."""
    source = dedent(
        """
        # comment to hello 1
        # comment to hello 2

        hello = 'hello' # comment to hello 3
        """
    )
    nodes = parse(source).body
    assert nodes[0].value == "# comment to hello 1"
    assert not nodes[0].inline
    assert nodes[1].value == "# comment to hello 2"
    assert not nodes[1].inline
    assert nodes[3].value == "# comment to hello 3"
    assert nodes[3].inline


def test_unrelated_comment():
    """Comment after statement"""
    source = dedent(
        """
        hello = 'hello'
        # unrelated comment
        """
    )
    nodes = parse(source).body
    assert len(nodes) == 2
    assert isinstance(nodes[1], Comment)
    assert not nodes[1].inline


def test_comment_to_function():
    """Comments to function and expression inside."""
    source = dedent(
        """
        # comment to function 'foo'
        def foo(*args, **kwargs):
            print(args, kwargs) # comment to print
        """
    )
    nodes = parse(source).body
    assert len(nodes) == 2
    assert nodes[0].value == "# comment to function 'foo'"
    assert not nodes[0].inline
    function_node = nodes[1]
    assert function_node.body[1].value == "# comment to print"
    assert function_node.body[1].inline


def test_comment_to_class():
    """Comments to class, its method and variable."""
    source = dedent(
        """
        # comment to class 'Foo'
        class Foo:
            var = "Foo var"    # comment to 'Foo.var'

            # comment to method 'foo'
            def foo(self):
                ...
        """
    )
    nodes = parse(source).body

    assert len(nodes) == 2
    assert nodes[0].value == "# comment to class 'Foo'"
    assert not nodes[0].inline
    class_body = nodes[1].body
    assert isinstance(class_body[0], ast.Assign)
    assert isinstance(class_body[1], Comment)
    assert class_body[1].inline
    assert isinstance(class_body[2], Comment)
    assert not class_body[2].inline
    assert isinstance(class_body[3], ast.FunctionDef)


def test_parse_again():
    """We can parse AstNode objects."""
    source = """hello = 'hello' # comment to hello"""
    nodes = parse(parse(source)).body
    assert isinstance(nodes[1], Comment)
    assert nodes[1].inline


def test_parse_ast():
    """We can parse ast.AST objects."""
    source = """hello = 'hello' # comment to hello"""
    assert parse(ast.parse(source))


def test_multiple_statements_in_line():
    """It's possible to parse multiple statements in one line."""
    source = """hello = 'hello'; hello += ' world?'"""
    tree = parse(source)
    assert len(tree.body) == 2


def test_comment_to_multiple_statements():
    """Comment goes behind statements."""
    source = """a=1; b=2 # hello"""
    nodes = parse(source).body
    assert len(nodes) == 3
    assert isinstance(nodes[0], ast.Assign)
    assert isinstance(nodes[1], ast.Assign)
    assert isinstance(nodes[2], Comment)
    assert nodes[2].inline


def test_comments_to_if():
    """Comments to if/elif/else blocks."""
    source = dedent(
        """
        if a > b: # if comment
            print('bigger')
        elif a == b: # elif comment
            print('equal')
        else: # else comment
            print('less')
        """
    )
    nodes = parse(source).body
    assert len(nodes) == 1  # IF node
    body_nodes = nodes[0].body
    assert len(body_nodes) == 2
    assert isinstance(body_nodes[0], Comment)
    assert body_nodes[0].inline
    assert isinstance(body_nodes[1], ast.Expr)

    orelse_nodes = nodes[0].orelse
    assert len(orelse_nodes) == 1  # ast.parse changes elif to nested if-else
    orelse_if_nodes = orelse_nodes[0].body
    assert len(orelse_if_nodes) == 2
    assert isinstance(orelse_if_nodes[0], Comment)
    assert orelse_if_nodes[0].inline
    assert isinstance(orelse_if_nodes[1], ast.Expr)

    orelse_else_nodes = orelse_nodes[0].orelse
    assert len(orelse_else_nodes) == 2
    assert isinstance(orelse_else_nodes[0], Comment)
    assert orelse_else_nodes[0].inline
    assert isinstance(orelse_else_nodes[1], ast.Expr)


def test_comments_to_for():
    """Comments to for/else blocks."""
    source = dedent(
        """
        for i in range(10): # for comment
            continue    # continue comment
        else:   # else comment
            pass    # pass comment
        """
    )
    nodes = parse(source).body
    assert len(nodes) == 1  # FOR node
    body_nodes = nodes[0].body
    assert len(body_nodes) == 3
    assert isinstance(body_nodes[0], Comment)
    assert isinstance(body_nodes[1], ast.Continue)
    assert isinstance(body_nodes[2], Comment)

    orelse_nodes = nodes[0].orelse
    assert len(orelse_nodes) == 3
    assert isinstance(orelse_nodes[0], Comment)
    assert isinstance(orelse_nodes[1], ast.Pass)
    assert isinstance(orelse_nodes[2], Comment)


def test_comments_to_try():
    """Comments to try/except/else/finally blocks."""
    source = dedent(
        """
        try:    # try comment
            1 / 0   # expr comment
        except ValueError:  # except ValueError comment
            pass    # pass comment
        except KeyError:    # except KeyError
            pass    # pass comment
        else:   # else comment
            print() # print comment
        finally:    # finally comment
            print() # print comment
        """
    )

    nodes = parse(source).body
    assert len(nodes) == 1  # TRY node
    body_nodes = nodes[0].body
    assert len(body_nodes) == 3
    assert isinstance(body_nodes[0], Comment)
    assert isinstance(body_nodes[1], ast.Expr)
    assert isinstance(body_nodes[2], Comment)

    handlers_nodes = nodes[0].handlers
    assert len(handlers_nodes) == 2
    for h_node in handlers_nodes:
        handler_nodes = h_node.body
        assert len(handler_nodes) == 3
        assert isinstance(handler_nodes[0], Comment)
        assert isinstance(handler_nodes[1], ast.Pass)
        assert isinstance(handler_nodes[2], Comment)

    else_nodes = nodes[0].orelse
    assert len(else_nodes) == 3
    assert isinstance(else_nodes[0], Comment)
    assert isinstance(else_nodes[1], ast.Expr)
    assert isinstance(else_nodes[2], Comment)

    finalbody_nodes = nodes[0].finalbody
    assert len(finalbody_nodes) == 3
    assert isinstance(finalbody_nodes[0], Comment)
    assert isinstance(finalbody_nodes[1], ast.Expr)
    assert isinstance(finalbody_nodes[2], Comment)


def test_comment_to_multiline_expr():
    """Comment to multilined expr goes first."""
    source = dedent(
        """
        if a:
            (b if b >=
                0 else 1)    # some comment
        """
    )
    if_node = parse(source).body[0]
    body_nodes = if_node.body
    assert len(body_nodes) == 2
    assert isinstance(body_nodes[0], ast.Expr)
    assert isinstance(body_nodes[1], Comment)
    assert body_nodes[1].inline


@pytest.mark.xfail(reason="https://github.com/t3rn0/ast-comments/issues/13")
def test_comment_in_multilined_list():
    """Comment to element of the list stays inside the list."""
    source = dedent(
        """
        lst = [
            1  # comment to element
        ]
        """
    )
    assert len(parse(source).body) == 1

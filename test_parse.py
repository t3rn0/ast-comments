"""Tests for `ast_comments.parse`."""

import ast
from textwrap import dedent

from ast_comments import Comment, parse


def test_single_comment_in_tree():
    """Parsed tree has Comment node."""
    source = """# comment"""
    nodes = parse(source).body
    assert len(nodes) == 1
    assert isinstance(nodes[0], Comment)


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


def test_inline_comment_after_statement():
    """Inlined comment goes before statement."""
    source = """hello = 'hello' # comment to hello"""
    nodes = parse(source).body
    assert len(nodes) == 2
    assert isinstance(nodes[0], Comment)


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
    assert nodes[1].value == "# comment to hello 2"
    assert nodes[2].value == "# comment to hello 3"


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
    function_node = nodes[1]
    assert function_node.body[0].value == "# comment to print"


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
    class_body = nodes[1].body
    assert isinstance(class_body[0], Comment)
    assert isinstance(class_body[1], ast.Assign)
    assert isinstance(class_body[2], Comment)
    assert isinstance(class_body[3], ast.FunctionDef)


def test_parse_again():
    """We can parse AstNode objects."""
    source = """hello = 'hello' # comment to hello"""
    nodes = parse(parse(source)).body
    assert isinstance(nodes[0], Comment)


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
    """Comment goes before statements."""
    source = """a=1; b=2 # hello"""
    nodes = parse(source).body
    assert len(nodes) == 3
    assert isinstance(nodes[0], Comment)
    assert isinstance(nodes[1], ast.Assign)
    assert isinstance(nodes[2], ast.Assign)


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
    assert isinstance(body_nodes[1], ast.Expr)

    orelse_nodes = nodes[0].orelse
    assert len(orelse_nodes) == 1  # ast.parse changes elif to nested if-else
    orelse_if_nodes = orelse_nodes[0].body
    assert len(orelse_if_nodes) == 2
    assert isinstance(orelse_if_nodes[0], Comment)
    assert isinstance(orelse_if_nodes[1], ast.Expr)

    orelse_else_nodes = orelse_nodes[0].orelse
    assert len(orelse_else_nodes) == 2
    assert isinstance(orelse_else_nodes[0], Comment)
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
    assert isinstance(body_nodes[1], Comment)
    assert isinstance(body_nodes[2], ast.Continue)

    orelse_nodes = nodes[0].orelse
    assert len(orelse_nodes) == 3
    assert isinstance(orelse_nodes[0], Comment)
    assert isinstance(orelse_nodes[1], Comment)
    assert isinstance(orelse_nodes[2], ast.Pass)


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
    assert len(nodes) == 1  # FOR node
    body_nodes = nodes[0].body
    assert len(body_nodes) == 3
    assert isinstance(body_nodes[0], Comment)
    assert isinstance(body_nodes[1], Comment)
    assert isinstance(body_nodes[2], ast.Expr)

    handlers_nodes = nodes[0].handlers
    assert len(handlers_nodes) == 2
    for h_node in handlers_nodes:
        handler_nodes = h_node.body
        assert len(handler_nodes) == 3
        assert isinstance(handler_nodes[0], Comment)
        assert isinstance(handler_nodes[1], Comment)
        assert isinstance(handler_nodes[2], ast.Pass)

    else_nodes = nodes[0].orelse
    assert len(else_nodes) == 3
    assert isinstance(else_nodes[0], Comment)
    assert isinstance(else_nodes[1], Comment)
    assert isinstance(else_nodes[2], ast.Expr)

    finalbody_nodes = nodes[0].finalbody
    assert len(finalbody_nodes) == 3
    assert isinstance(finalbody_nodes[0], Comment)
    assert isinstance(finalbody_nodes[1], Comment)
    assert isinstance(finalbody_nodes[2], ast.Expr)

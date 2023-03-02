"""Tests for `ast_comments.unparse`.
From https://docs.python.org/3.9/library/ast.html
```
ast.unparse(ast_obj)
    Unparse an ast.AST object and generate a string with code that would produce an equivalent
    ast.AST object if parsed back with ast.parse().
```
Same source samples as in test_parse.py are used.
"""

from textwrap import dedent

from ast_comments import dump, parse, unparse


def _test_unparse(source: str):
    source_tree = parse(source)
    equivalent_tree = parse(unparse(source_tree))
    assert dump(source_tree) == dump(equivalent_tree)


def test_single_comment_in_tree():
    source = """# comment"""
    _test_unparse(source)


def test_separate_line_single_line():
    source = dedent(
        """
        # comment to hello
        hello = 'hello'
        """
    )
    _test_unparse(source)


def test_inline_comment_before_statement():
    source = """hello = 'hello' # comment to hello"""
    _test_unparse(source)


def test_separate_line_multiline():
    """Multiple comments to the following line."""
    source = dedent(
        """
        # comment to hello 1
        # comment to hello 2
        hello = 'hello'
        """
    )
    _test_unparse(source)


def test_multiline_and_inline_combined():
    """Multiple comments to the following line combined with inline comment."""
    source = dedent(
        """
        # comment to hello 1
        # comment to hello 2

        hello = 'hello' # comment to hello 3
        """
    )
    _test_unparse(source)


def test_unrelated_comment():
    """Comment after statement"""
    source = dedent(
        """
        hello = 'hello'
        # unrelated comment
        """
    )
    _test_unparse(source)


def test_comment_to_function():
    """Comments to function and expression inside."""
    source = dedent(
        """
        # comment to function 'foo'
        def foo(*args, **kwargs):
            print(args, kwargs) # comment to print
        """
    )
    _test_unparse(source)


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
    _test_unparse(source)


def test_multiple_statements_in_line():
    """It's possible to parse multiple statements in one line."""
    source = """hello = 'hello'; hello += ' world?'"""
    _test_unparse(source)


def test_comment_to_multiple_statements():
    """Comment goes before statements."""
    source = """a=1; b=2 # hello"""
    _test_unparse(source)


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
    _test_unparse(source)


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
    _test_unparse(source)


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
    _test_unparse(source)


def test_comment_to_multiline_expr():
    source = dedent(
        """
        if a:
            (b if b >=
                0 else 1)    # some comment
        """
    )
    _test_unparse(source)


def test_inline_comments_stay_inline():
    source = dedent(
        """
        class Foo:  # c1
            pass
        """
    )
    _test_unparse(source)
    unparsed_source = unparse(parse(source))
    assert "class Foo:  # c1" in unparsed_source


def test_comments_in_body():
    source = dedent(
        """
        class Foo: 
            # c1
            pass
        """
    )
    _test_unparse(source)
    unparsed_source = unparse(parse(source))
    assert "class Foo:\n    # c1" in unparsed_source

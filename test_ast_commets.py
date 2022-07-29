from textwrap import dedent

import ast_comments as astcom


def test_comments_attr_in_nodes():
    """Comment in the node attributes"""
    source = """hello = 'hello'"""
    tree = astcom.parse(source)
    node = tree.body[0]
    assert hasattr(node, "comments")


def test_inline():
    """Comment to the same line"""
    source = """hello = 'hello' # comment to hello"""
    tree = astcom.parse(source)
    node = tree.body[0]
    assert node.comments == ("comment to hello",)


def test_separate_line_single_line():
    """Comment to the following line"""
    source = dedent(
        """
        # comment to hello
        hello = 'hello'
        """
    )
    tree = astcom.parse(source)
    node = tree.body[0]
    assert node.comments == ("comment to hello",)


def test_separate_line_multiline():
    """Multiple comments to the following line"""
    source = dedent(
        """
        # comment to hello 1
        # comment to hello 2
        hello = 'hello'
        """
    )
    tree = astcom.parse(source)
    node = tree.body[0]
    assert node.comments == (
        "comment to hello 1",
        "comment to hello 2",
    )


def test_multiline_and_inline_combined():
    """Multiple comments to the following line combined with inline comment"""
    source = dedent(
        """
        # comment to hello 1
        # comment to hello 2

        hello = 'hello' # comment to hello 3
        """
    )
    tree = astcom.parse(source)
    node = tree.body[0]
    assert node.comments == (
        "comment to hello 1",
        "comment to hello 2",
        "comment to hello 3",
    )


def test_unrelated_comment():
    """Unrelated comment goes to nothing"""
    source = dedent(
        """
        hello = 'hello'
        # unrelated comment
        """
    )
    tree = astcom.parse(source)
    node = tree.body[0]
    assert node.comments == ()


def test_comment_to_function():
    """Unrelated comment goes to nothing"""
    source = dedent(
        """
        # comment to function 'foo'
        def foo(*args, **kwargs):
            print(args, kwargs) # comment to print
        """
    )
    tree = astcom.parse(source)

    function_node = tree.body[0]
    assert function_node.comments == ("comment to function 'foo'",)

    expr_node = function_node.body[0]
    assert expr_node.comments == ("comment to print",)


def test_comment_to_class():
    """Unrelated comment goes to nothing"""
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
    tree = astcom.parse(source)

    class_node = tree.body[0]
    assert class_node.comments == ("comment to class 'Foo'",)

    var_node, method_node = class_node.body
    assert var_node.comments == ("comment to 'Foo.var'",)
    assert method_node.comments == ("comment to method 'foo'",)

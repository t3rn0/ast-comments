# ast-comments

An extension to the built-in `ast` module. 
Finds comments in source code and adds them to the parsed tree.

## Installation
```
pip install ast-comments
```

## Usage

There is no difference in usage between `ast` and `ast-comments`
```
>>> from ast_comments import *
>>> tree = parse("hello = 'hello' # comment to hello")
```
Parsed tree is instance of the original ast.Module object.
The only difference is there is a new type of tree node: Comment
```
>>> tree
<_ast.Module object at 0x7ffba52322e0>
>>> tree.body
[<ast_comments.Comment object at 0x10c1b6160>, <_ast.Assign object at 0x10bd217c0>]
>>> tree.body[0].value
'# comment to hello'
>>> dump(tree)
"Module(body=[Comment(value='# comment to hello'), Assign(targets=[Name(id='hello', ctx=Store())], value=Constant(value='hello', kind=None), type_comment=None)], type_ignores=[])"
```
If you have python3.9 or above it's also possible to unparse the tree object with its comments preserved.
```
>>> print(unparse(tree))
# comment to hello
hello = 'hello'
```
More examples can be found in test_parse.py and test_unparse.py.

## Notes
1. Right now it is assumed that there is no difference between inlined comments and regular. 
All inlined comments become regular after the tree object is unparsed.

2. Inlined comments for class- (def-, if-, ...) block shift "inside" body of the corresponding block:
    ```
    >>> source = """class Foo: # c1
    ...     pass
    ... """
    >>> unparse(parse(source))
    >>> print(unparse(parse(source)))
    class Foo:
        # c1
        pass
    ```

## Contributing
You are welcome to open an issue or create a pull request
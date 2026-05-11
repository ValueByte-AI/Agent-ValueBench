"""
Extract all method signatures, docstrings, and source code fragments from a source code string for a specified class
"""
import ast
from pathlib import Path


def normalize_source(src: str) -> str:
    s = src.strip()
    if (s.startswith(("'", '"')) and s.endswith(("'", '"'))):
        try:
            import ast as pyast
            s = pyast.literal_eval(s)  # "'code\\n...'" -> "code\n..."
        except Exception:
            pass
    return s

def ann_to_str(node):
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        base = ann_to_str(node.value)
        sl = node.slice
        if isinstance(sl, ast.Index):  # py3.8
            sub = ann_to_str(sl.value)
        elif isinstance(sl, ast.Tuple):
            sub = ", ".join(ann_to_str(elt) for elt in sl.elts)
        else:
            sub = ann_to_str(sl)
        return f"{base}[{sub}]"
    if isinstance(node, ast.Constant):
        return type(node.value).__name__
    if isinstance(node, ast.Str):  # py3.8
        return "str"
    return "unknown"

def default_to_str(node):
    if node is None:
        return None
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            return f"{node.func.id}(...)"
        if isinstance(node.func, ast.Attribute):
            return f"{node.func.attr}(...)"
        return "call(...)"
    if isinstance(node, ast.Dict):
        return "{...}"
    if isinstance(node, ast.List):
        return "[...]"
    if isinstance(node, ast.Tuple):
        return "(...)"
    return "..."

def build_signature(func_node: ast.FunctionDef, include_self: bool = True):
    args_obj = func_node.args
    params = []

    def add_param(name, ann, default, kind):
        params.append({
            "name": name,
            "type": ann_to_str(ann),
            "default": default_to_str(default),
            "kind": kind,  # Display-only metadata; not used for deeper parsing.
        })

    # positional-only (py3.8+)
    posonly = getattr(args_obj, "posonlyargs", [])
    for a in posonly:
        add_param(a.arg, a.annotation, None, "positional-only")

    # positional-or-keyword
    total = len(args_obj.args)
    defaults = list(args_obj.defaults or [])
    nd = len(defaults)
    for i, a in enumerate(args_obj.args):
        default = defaults[i - (total - nd)] if nd and i >= total - nd else None
        add_param(a.arg, a.annotation, default, "positional-or-keyword")

    # *args
    if args_obj.vararg:
        add_param(args_obj.vararg.arg, args_obj.vararg.annotation, None, "vararg")

    # kw-only
    kw_defaults = list(args_obj.kw_defaults or [])
    for i, a in enumerate(args_obj.kwonlyargs):
        default = kw_defaults[i] if i < len(kw_defaults) else None
        add_param(a.arg, a.annotation, default, "kwonly")

    # **kwargs
    if args_obj.kwarg:
        add_param(args_obj.kwarg.arg, args_obj.kwarg.annotation, None, "kwarg")

    if not include_self and params and params[0]["name"] in ("self", "cls"):
        params = params[1:]

    return {"parameters": params, "return": ann_to_str(func_node.returns)}

def extract_class_methods_from_source(source_str: str, class_name: str, include_self: bool = True):
    """
    Extract method signatures, docstrings, and source fragments for class_name from source_str.
    """
    src = normalize_source(source_str)   # Normalize source text.
    tree = ast.parse(src, type_comments=True)  # Build AST.
    lines = src.splitlines()  # Used to extract source fragments.
    func_details = {}

    # Find the target class among top-level nodes.
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            # Visit methods defined directly on the class body.
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    sig = build_signature(item, include_self=include_self)
                    doc = ast.get_docstring(item) or ""

                    # Python 3.8+ exposes end_lineno directly.
                    if hasattr(item, "end_lineno") and item.end_lineno is not None:
                        # Preserve original indentation and formatting in the source fragment.
                        func_lines = lines[item.lineno - 1 : item.end_lineno]
                        func_code = "\n".join(func_lines)
                    else:
                        # Python 3.7 and earlier do not expose end_lineno.
                        func_code = ""  # Token scanning could be added if older Python support is needed.

                    func_details[item.name] = {
                        "signature": sig,
                        "doc": doc.strip(),
                        "source_code": func_code
                    }
            break
    # Remove __init__.
    func_details.pop("__init__", None)
    return func_details


def extract_class_methods(input_data, class_name: str, include_self: bool = True):
    # Accept either a path or a source-code string, including quoted string literals.
    try:
        p = Path(input_data)
        if p.exists():
            source = p.read_text(encoding="utf-8")
        else:
            source = str(input_data)
    except Exception:
        source = str(input_data)
    return extract_class_methods_from_source(source, class_name, include_self=include_self)

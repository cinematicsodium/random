def get_code_data():
    import ast
    import os
    import json
    from icecream import ic

    def retrieve_code(path: str) -> str:
        with open(path, "r") as f:
            code = f.read()
            if code:
                return code
            error_message = "Code not found in path: {path}".format(path=path)
            raise ValueError(error_message)

    def get_defined_functions(code):
        tree = ast.parse(code)
        return [
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        ]

    def get_defined_variables(code):
        tree = ast.parse(code)
        variable_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variable_names.append(target.id)
        return variable_names

    def get_defined_custom_items(code):
        tree = ast.parse(code)
        custom_item_names = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        ]
        return custom_item_names

    paths: list[str] = [
        r"main.py",
        r"constants.py",
        r"modules.py",
        r"notices.py",
        r"utils.py",
    ]
    path_data: dict[str, dict[str, list[str]]] = {}
    for path in paths:
        directory = os.path.basename(os.path.dirname(path))
        if not directory in path_data:
            path_data[directory] = {}
        path_name = os.path.basename(path)
        path_data[directory][path_name] = {}
        try:
            code = retrieve_code(path)
            path_data[directory][path_name]["functions"] = list(set(get_defined_functions(code)))
            ic(path_data[directory][path_name]["functions"])
            path_data[directory][path_name]["variables"] = list(set(get_defined_variables(code)))
            ic(path_data[directory][path_name]["variables"])
            path_data[directory][path_name]["items"] = list(set(get_defined_custom_items(code)))
            ic(path_data[directory][path_name]["variables"])
        except Exception as e:
            print(
                "Error parsing code for path: {path}\n\n{e}".format(path=path_name, e=e)
            )

    with open("file.json", "w") as f:
        json.dump(path_data, f, indent=4)

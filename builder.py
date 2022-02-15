"""
src配下のファイルを一つのファイルにくっつける処理を行う。
"""
from pathlib import Path
from typing import Dict, List, Tuple


def merge_import_statements(import_states: List[str], lib_names: List[str]) -> List[str]:
    """import文をまとめる

    Args:
        import_states (List[str]): import文のリスト. import hoge / from hoge import fugaの両方の形式を含む。
        lib_names (List[str], optional): importで無視すべきモジュールのリスト.

    Returns:
        List[str]: 同一モジュールからのimportをくっつけたimport文のリスト
    """
    import_states = list(set(import_states))
    from_import_states_holder: Dict[str, List[str]] = {}

    result_import_statements = []

    for state in import_states:
        if state.startswith("from"):
            # from typing import List みたいな時
            splitted = state.split(" ")
            lib_name = splitted[1]
            if lib_name in lib_names:
                continue

            imps = state[state.index("import") + len("import "):].replace("\n", "").split(", ")
            if lib_name in from_import_states_holder:
                from_import_states_holder[lib_name].extend(imps)

            else:
                from_import_states_holder[lib_name] = imps

        else:
            result_import_statements.append(state)

    for lib_name, import_list in from_import_states_holder.items():
        imps = list(set(import_list))
        import_state = ", ".join(imps)
        state = f"from {lib_name} import {import_state}\n"
        result_import_statements.append(state)

    return result_import_statements


def delete_block_comment(codes: List[str]) -> List[str]:
    """ \"\"\"で定義されるコメント行を消去する """
    result_codes = []

    in_block_comment = False
    for row in codes:
        startswith_comment = row.lstrip().startswith("\"\"\"")
        if startswith_comment and not in_block_comment:
            in_block_comment = True
            continue

        if not startswith_comment and in_block_comment:
            continue

        if startswith_comment and in_block_comment:
            in_block_comment = False

        else:
            result_codes.append(row)

    return result_codes


def get_codes_with_splitted_import_states(file: Path) -> Tuple[List[str], List[str]]:
    """ import文を分離したソースコードを取得する """
    import_statements = []
    codes = []

    with open(file, "r", encoding="utf-8") as f:
        for row in f.readlines():
            if row.startswith("import") or row.startswith("from"):
                import_statements.append(row)

            else:
                codes.append(row)

    return import_statements, codes


def main():
    src = Path("./src")

    main_file = src / "main.py"
    dist = Path("bin/main.py")

    import_statements: List[str]
    main_code: List[str]

    import_statements, main_code = get_codes_with_splitted_import_states(main_file)

    lib_src_codes: List[str] = []

    libs = src.glob("*.py")
    lib_names: List[str] = []

    for lib in libs:
        if lib.stem == "main":
            continue
        lib_names.append(lib.stem)
        lib_imp_states, lib_code = get_codes_with_splitted_import_states(lib)
        import_statements.extend(lib_imp_states)
        lib_code = delete_block_comment(lib_code)
        lib_src_codes.extend(lib_code)

    # import文を整理
    import_statements = merge_import_statements(import_statements, lib_names)

    new_code = f"{''.join(import_statements)}{''.join(lib_src_codes)}{''.join(main_code)}"

    with open(dist, "w", encoding="utf-8") as f:
        f.writelines(new_code)


if __name__ == '__main__':
    main()

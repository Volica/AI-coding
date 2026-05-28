import time
from pathlib import Path


CASES = [
    (5, 2, 3, 12),
    (6, 3, 4, 72),
    (10, 4, 5, 1080),
    (20, 5, 8, 3386880),
    (100, 10, 20, 404871385),
    (1000, 500, 99999, 578108381),
    (3, 5, 10, 0),
    (1000, 1000, 100000, 457992974),
]


def load_solve_from_file(path):
    namespace = {}
    code = Path(path).read_text(encoding="utf-8")
    exec(code, namespace)
    assert "solve" in namespace, "代码中必须定义 solve(n, k, m)"
    assert callable(namespace["solve"]), "solve 必须是可调用函数"
    return namespace["solve"]


def test_solve_correctness_and_speed():
    solve = load_solve_from_file(Path(__file__).with_name("solution.py"))

    start = time.perf_counter()
    for n, k, m, expected in CASES:
        actual = solve(n, k, m)
        assert actual == expected, (
            f"solve({n}, {k}, {m}) 结果错误："
            f"期望 {expected}，实际 {actual}"
        )
    elapsed = time.perf_counter() - start

    assert elapsed < 1.0, f"执行时间过长：{elapsed:.4f}s，要求 1 秒内完成"


if __name__ == "__main__":
    test_solve_correctness_and_speed()
    print("全部组合数学求解器测试通过")

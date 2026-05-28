import json


EXPECTED_CASES = [
    {
        "input": "草莓3斤，需要果切，节日期间，需要环保袋",
        "expected": {"total_bill": 80, "fruit_cost": 59},
    },
    {
        "input": "苹果2斤，葡萄4斤，不要果切，要环保袋",
        "expected": {"total_bill": 72, "fruit_cost": 70},
    },
    {
        "input": "蓝莓1斤，樱桃3斤，节日期间，不果切，不需要袋子",
        "expected": {"total_bill": 188, "fruit_cost": 156},
    },
    {
        "input": "香蕉3斤，西瓜5斤，火龙果2斤，切成果盘，普通工作日",
        "expected": {"total_bill": 84, "fruit_cost": 64},
    },
    {
        "input": "芒果3斤，猕猴桃3斤，柚子1斤，需要切好，春节期间，另加一个购物袋",
        "expected": {"total_bill": 119, "fruit_cost": 83},
    },
]


MODEL_OUTPUTS = [
    '{"total_bill":80,"fruit_cost":59}',
    '{"total_bill":72,"fruit_cost":70}',
    '{"total_bill":188,"fruit_cost":156}',
    '{"total_bill":84,"fruit_cost":64}',
    '{"total_bill":119,"fruit_cost":83}',
]


def assert_valid_json_only(raw_output):
    raw_output = raw_output.strip()
    parsed = json.loads(raw_output)

    assert isinstance(parsed, dict), "模型输出必须是 JSON 对象"
    assert set(parsed) == {"total_bill", "fruit_cost"}, "只能输出 total_bill 和 fruit_cost 两个字段"
    assert isinstance(parsed["total_bill"], (int, float)), "total_bill 必须是数字"
    assert isinstance(parsed["fruit_cost"], (int, float)), "fruit_cost 必须是数字"

    return parsed


def test_model_outputs():
    assert len(MODEL_OUTPUTS) == len(EXPECTED_CASES), "模型输出数量必须与测试用例数量一致"

    for index, (case, raw_output) in enumerate(zip(EXPECTED_CASES, MODEL_OUTPUTS), start=1):
        actual = assert_valid_json_only(raw_output)
        expected = case["expected"]

        assert actual == expected, (
            f"第 {index} 条用例失败\n"
            f"输入：{case['input']}\n"
            f"期望：{expected}\n"
            f"实际：{actual}"
        )


if __name__ == "__main__":
    test_model_outputs()
    print("全部测试通过")

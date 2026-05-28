import json


EXPECTED_CASES = [
    {
        "input": "昨晚11点半打车回家，一共跑了14公里，交了10块钱过路费，账户里有一张满40减8元的券和一张75折券",
        "expected": {"total_fare": 48, "base_fare": 51, "applied_discount": "75折"},
    },
    {
        "input": "下午3点打车去公司，全程2.5公里，停车费5元，没有优惠券",
        "expected": {"total_fare": 18, "base_fare": 13, "applied_discount": "无"},
    },
    {
        "input": "晚上11点20分出发，打车11.2公里，没有附加费，有一张满40减10元券和一张75折券",
        "expected": {"total_fare": 30, "base_fare": 40, "applied_discount": "满40减10"},
    },
    {
        "input": "凌晨1点打车去机场，一共5公里，路桥费3元，账户里有满30减5和9折券",
        "expected": {"total_fare": 20, "base_fare": 19, "applied_discount": "9折"},
    },
    {
        "input": "夜里2点半坐网约车跨城，全程18公里，高速费20元，停车费5元，有满60减12元券和85折券",
        "expected": {"total_fare": 81, "base_fare": 68, "applied_discount": "满60减12"},
    },
]


MODEL_OUTPUTS = [
    '{"total_fare":48,"base_fare":51,"applied_discount":"75折"}',
    '{"total_fare":18,"base_fare":13,"applied_discount":"无"}',
    '{"total_fare":30,"base_fare":40,"applied_discount":"满40减10"}',
    '{"total_fare":20,"base_fare":19,"applied_discount":"9折"}',
    '{"total_fare":81,"base_fare":68,"applied_discount":"满60减12"}',
]


def assert_valid_json_only(raw_output):
    raw_output = raw_output.strip()
    parsed = json.loads(raw_output)

    assert isinstance(parsed, dict), "模型输出必须是 JSON 对象"
    assert set(parsed) == {
        "total_fare",
        "base_fare",
        "applied_discount",
    }, "只能输出 total_fare、base_fare、applied_discount 三个字段"
    assert isinstance(parsed["total_fare"], (int, float)), "total_fare 必须是数字"
    assert isinstance(parsed["base_fare"], (int, float)), "base_fare 必须是数字"
    assert isinstance(parsed["applied_discount"], str), "applied_discount 必须是字符串"

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
    print("全部网约车计费测试通过")

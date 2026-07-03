from loadgen.analyze import analyze


def test_analyze_records():
    records = [
        {
            "status_code": 200,
            "latency": 2.0,
            "ttft": 0.5,
            "tpot": 0.1,
            "prompt_tokens": 100,
            "output_tokens": 20,
            "start_time": 0,
            "end_time": 2,
        },
        {
            "status_code": 599,
            "latency": 1.0,
            "ttft": None,
            "tpot": None,
            "prompt_tokens": 0,
            "output_tokens": 0,
            "start_time": 1,
            "end_time": 2,
        },
    ]
    summary = analyze(records)
    assert summary["requests"] == 2
    assert summary["success"] == 1
    assert summary["error_rate"] == 0.5


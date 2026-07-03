from simulator.tenant_quota import simulate


def test_tenant_quota_sim_runs():
    config = {
        "seed": 1,
        "requests": 50,
        "request_rate": 5,
        "long_context_ratio": 0.2,
        "long_output_ratio": 0.2,
        "low_priority_threshold": 1,
        "tenants": {
            "gold": {
                "priority": 10,
                "requests_per_minute": 100,
                "tokens_per_minute": 100000,
                "max_context_tokens": 12000,
            },
            "bronze": {
                "priority": 1,
                "requests_per_minute": 10,
                "tokens_per_minute": 10000,
                "max_context_tokens": 4096,
            },
        },
    }
    result = simulate(config, "token-level")
    assert result["accepted"] + result["rejected"] + result["throttled"] == 50


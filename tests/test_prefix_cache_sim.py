from simulator.prefix_cache import simulate


def test_prefix_cache_sim_runs():
    result = simulate(
        {
            "seed": 1,
            "replicas": 2,
            "requests": 50,
            "request_rate": 5,
            "cache_capacity": 8,
            "prefix_cardinality": 10,
            "hot_prefixes": 2,
            "hot_prefix_ratio": 0.8,
        },
        "prefix-aware",
    )
    assert result["summary"]["requests"] == 50
    assert 0 <= result["summary"]["hit_ratio"] <= 1


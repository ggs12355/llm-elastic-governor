from simulator.multi_replica import simulate


def test_multi_replica_sim_runs():
    result = simulate(
        {
            "seed": 1,
            "duration_seconds": 10,
            "request_rate": 2,
            "initial_replicas": 1,
            "max_replicas": 2,
            "cold_start_seconds": 5,
            "scale_queue_threshold": 2,
        },
        "least-queue",
    )
    assert result["summary"]["requests"] > 0
    assert "latency" in result["summary"]


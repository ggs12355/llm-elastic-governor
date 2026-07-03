from simulator.topology_scheduler import simulate


def test_topology_scheduler_sim_runs():
    result = simulate(
        {
            "seed": 1,
            "nodes": 2,
            "gpus_per_node": 2,
            "gpus_per_numa": 1,
            "gpu_memory_gb": 24,
            "jobs": 10,
        },
        "topology-aware",
    )
    assert "success_rate" in result


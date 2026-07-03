from metrics.parser import parse_nvidia_smi_csv


def test_parse_nvidia_smi_csv():
    text = "0, NVIDIA GeForce RTX 4090, 87, 21000, 24564, 66, 320.5\n"
    samples = parse_nvidia_smi_csv(text, timestamp=1.5)
    assert len(samples) == 1
    assert samples[0].index == 0
    assert samples[0].memory_ratio > 0.8


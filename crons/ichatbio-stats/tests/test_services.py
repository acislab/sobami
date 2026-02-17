from src import services


def test_check_all():
    service_data = (
        "ichatbio.org https://ichatbio.org",
        "test idigbio https://idigbio.org",
    )

    report = dict(services.check_all(service_data))

    assert "ichatbio.org" in report
    assert len(report) == 2
    assert all(report.values())

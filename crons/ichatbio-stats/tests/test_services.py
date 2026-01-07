import services


def test_check_all():
    agents = (
        "ala",
        "data-handler",
        "gbif",
        "globi",
        "idigbio",
        "map-maker",
        "obis",
        "worms",
    )

    report = dict(status.check_all(agents))

    assert "ichatbio.org" in report
    assert len(report) == 9
    assert all(report.values())

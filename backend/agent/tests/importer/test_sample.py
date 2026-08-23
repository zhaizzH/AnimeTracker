from importer.main import _sample_ids, parse_args


def test_sample_ids_use_requested_strata_and_limit():
    items = (
        [(i, "1989-01-01") for i in range(1, 80)]
        + [(i, "2000-01-01") for i in range(100, 220)]
        + [(i, "2015-01-01") for i in range(300, 480)]
        + [(i, "2024-01-01") for i in range(500, 750)]
    )

    selected, distribution = _sample_ids(items, limit=500, strata=(50, 100, 150, 200))

    assert len(selected) == 500
    assert distribution == {"before_1990": 50, "1990_2009": 100, "2010_2019": 150, "2020_plus": 200}


def test_sample_ids_borrows_from_adjacent_strata_when_short():
    selected, distribution = _sample_ids([(1, "1980-01-01"), (2, "2024-01-01"), (3, "2024-01-01")], limit=3, strata=(2, 0, 0, 1))

    assert selected == [1, 2, 3]
    assert distribution == {"before_1990": 1, "1990_2009": 0, "2010_2019": 0, "2020_plus": 2}


def test_sample_mode_and_limit_are_internal_cli_options():
    args = parse_args(["--mode", "sample", "--limit", "500"])

    assert args.mode == "sample"
    assert args.limit == 500

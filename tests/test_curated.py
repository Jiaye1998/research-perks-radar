from fetchers.curated import _looks_like_noise


def test_paper_and_preprint_hosts_are_noise():
    assert _looks_like_noise("Fast Correspondence-Free Lidar Odometry", "https://arxiv.org/abs/2401.00001")
    assert _looks_like_noise("Some Dataset Citation", "https://doi.org/10.1234/abcd")
    assert _looks_like_noise("A Study", "https://www.researchgate.net/publication/123")


def test_author_list_anchor_is_noise():
    assert _looks_like_noise(
        "Matheus P. Viana, Jianxu Chen, Theo A. Knijnenburg, Ritvik Vasan",
        "https://alleninstitute.org/resource",
    )


def test_real_programs_are_kept():
    assert not _looks_like_noise(
        "Gabriella Miller Kids First Pediatric Research Program",
        "https://registry.opendata.aws/kids-first/",
    )
    assert not _looks_like_noise(
        "Joint Remote Sensing Research Program",
        "https://jrsrp.org.au/",
    )
    assert not _looks_like_noise(
        "Apply for the Schmidt Science Fellowship",
        "https://schmidtsciencefellows.org/fellowship/",
    )

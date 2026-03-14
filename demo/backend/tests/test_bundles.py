from demo.backend.services.bundles import get_curated_bundles


def test_curated_bundles_resolve_from_artifacts():
    bundles = get_curated_bundles()
    assert set(bundles.keys()) == {"maize_uncertain", "maize_stable", "soybean_reference"}
    for bundle in bundles.values():
        assert "artifacts" in str(bundle.bundle_dir)
        assert "Local Files and Folders" not in str(bundle.bundle_dir)
        assert bundle.config_path.exists()
        assert bundle.model_path.exists()

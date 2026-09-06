"""M2: source config edits cannot alter a run's frozen protected profiles."""

import json
import shutil
from truss.runtime import TrussRun
from truss.config import load_member


def test_run_profiles_do_not_follow_source_edits(tmp_path, monkeypatch):
    source = tmp_path / "config"
    shutil.copytree("config", source)
    monkeypatch.setattr(
        "truss.runtime.broker_binary", lambda: tmp_path / "unused-mosquitto"
    )
    run = TrussRun(config_dir=source, runtime_root=tmp_path / "runs")
    frozen = run.snapshot_profiles()
    path = source / "member-a.json"
    profile = json.loads(path.read_text())
    profile["devices"][0]["control_policy"] = "flexible"
    profile["devices"][0]["baseline_w"] = 0
    path.write_text(json.dumps(profile))
    admitted = load_member(frozen / "member-a.json", run.policy.members[0])
    assert admitted.devices[0].control_policy == "protected"
    assert admitted.devices[0].baseline_w == admitted.devices[0].max_w

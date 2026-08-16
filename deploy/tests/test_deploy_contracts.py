from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_minio_backup_scripts_use_dedicated_mc_image():
    for relative in ("deploy/scripts/backup.sh", "deploy/scripts/restore.sh"):
        content = (ROOT / relative).read_text(encoding="utf-8")
        assert "MINIO_MC_IMAGE" in content
        assert "grep '^quay.io/minio/minio:'" not in content
        assert 'docker run --rm --entrypoint mc' in content


def test_ci_runs_dataset_and_offline_eval_gate():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "--ignore=tests/test_eval_dataset.py" not in workflow
    assert "python -m pytest -q" in workflow
    assert "python -m evals.runner --mode offline" in workflow
    assert "python -m pytest deploy/tests/test_deploy_contracts.py" in workflow


def test_ci_actions_use_node24_generations():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "actions/checkout@v6" in workflow
    assert "actions/setup-java@v5" in workflow
    assert "actions/setup-python@v6" in workflow
    assert "actions/setup-node@v6" in workflow
    for old_action in (
        "actions/checkout@v4",
        "actions/setup-java@v4",
        "actions/setup-python@v5",
        "actions/setup-node@v4",
    ):
        assert old_action not in workflow


def test_business_image_uses_the_maven_final_jar_name():
    pom = (ROOT / "backend/business/app/pom.xml").read_text(encoding="utf-8")
    dockerfile = (ROOT / "backend/business/Dockerfile").read_text(encoding="utf-8")
    assert "<finalName>app</finalName>" in pom
    assert "COPY --from=builder /build/app/target/app.jar /app/app.jar" in dockerfile
    assert "-DfinalName=app" not in dockerfile


def test_certbot_has_no_docker_socket_and_nginx_reloads_certificates():
    compose = (ROOT / "compose.prod.yml").read_text(encoding="utf-8")
    certbot = (ROOT / "deploy/certbot/init-cert.sh").read_text(encoding="utf-8")
    nginx = (ROOT / "deploy/nginx/bootstrap.sh").read_text(encoding="utf-8")
    assert "/var/run/docker.sock" not in compose
    assert "/var/run/docker.sock" not in certbot
    assert "nginx -s reload" in nginx


def test_non_root_requirement_targets_custom_application_images():
    for relative in ("backend/business/Dockerfile", "backend/agent/Dockerfile"):
        content = (ROOT / relative).read_text(encoding="utf-8")
        assert "USER app" in content

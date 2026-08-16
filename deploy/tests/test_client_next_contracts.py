"""新 Client 部署契约测试(opt-in, 未切换生产流量)。

覆盖: client-next 服务仅在 next-client profile 下启用且不发布端口;
nginx 代理模板无反代静态 SPA fallback、透传标准头部;
Dockerfile 非 root 运行且只拷贝 standalone 产物。
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_next_client_is_opt_in(compose_config):
    service = compose_config["services"]["client-next"]
    assert "next-client" in service["profiles"]
    assert service["expose"] == ["3000"]


def test_next_client_not_published_and_on_frontend_network(compose_config):
    service = compose_config["services"]["client-next"]
    assert "frontend" in service["networks"]
    assert "ports" not in service


def test_next_proxy_has_no_spa_fallback(nginx_template):
    assert "proxy_pass http://client-next:3000" in nginx_template
    assert "try_files $uri $uri/ /index.html" not in nginx_template


def test_next_proxy_forwards_standard_headers(nginx_template):
    for header in ("Host", "X-Real-IP", "X-Forwarded-For", "X-Forwarded-Proto", "X-Request-ID"):
        assert f"proxy_set_header {header}" in nginx_template


def test_next_container_is_non_root_and_copies_standalone():
    dockerfile = (ROOT / "frontend/apps/client/Dockerfile").read_text(encoding="utf-8")
    assert "USER nextjs" in dockerfile
    assert ".next/standalone" in dockerfile
    assert "COPY --from=builder" in dockerfile

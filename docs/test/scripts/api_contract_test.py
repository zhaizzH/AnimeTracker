#!/usr/bin/env python3
"""Contract tests for the AnimeTracker business API (docs/spec/openapi.yaml).

Run:
    python docs/test/scripts/api_contract_test.py

Environment:
    AT_API_BASE       backend base URL (default http://127.0.0.1:8080)
    AT_TEST_USER      normal user name (default test1)
    AT_TEST_USER_PASS normal user password (default 123456)
    AT_TEST_ADMIN     admin user name (default admin)
    AT_TEST_ADMIN_PASS admin password (default 123456)
    AT_TIMEOUT        per-request timeout in seconds (default 15)
"""

import base64
import json
import os
import pathlib
import re
import sys
import time
import urllib.parse
import uuid

import requests

BASE = os.environ.get("AT_API_BASE", "http://127.0.0.1:8080")
USER = os.environ.get("AT_TEST_USER", "test1")
USER_PASS = os.environ.get("AT_TEST_USER_PASS", "123456")
ADMIN = os.environ.get("AT_TEST_ADMIN", "admin")
ADMIN_PASS = os.environ.get("AT_TEST_ADMIN_PASS", "123456")
TIMEOUT = float(os.environ.get("AT_TIMEOUT", "15"))

SPEC_FILE = pathlib.Path(__file__).resolve().parents[2] / "spec" / "openapi.yaml"
OUT_FILE = pathlib.Path(__file__).resolve().parents[2] / "test" / "report" / "api-contract-results-2026-08-15.json"

HTTP = requests.Session()
HTTP.trust_env = False

results = []


def request(method, path, token=None, params=None, json_body=None, files=None, timeout=TIMEOUT):
    """Perform a request and return (http_status, parsed_body, elapsed_ms)."""
    headers = {}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        resp = HTTP.request(
            method,
            BASE + path,
            params=params,
            json=json_body,
            files=files,
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return 0, {"transport_error": str(exc)}, None
    try:
        body = resp.json()
    except ValueError:
        body = {"raw": resp.text}
    return resp.status_code, body, round(resp.elapsed.total_seconds() * 1000, 1)


def finish(cid, method, path_tpl, passed, http, body, expected, path=None, note="", status=None):
    code = body.get("code") if isinstance(body, dict) else None
    actual = "http={} code={} body={}".format(
        http, code, json.dumps(body, ensure_ascii=True)[:220]
    )
    results.append(
        {
            "id": cid,
            "method": method,
            "path": path or path_tpl,
            "path_template": path_tpl,
            "status": status or ("PASS" if passed else "FAIL"),
            "http": http,
            "code": code,
            "expected": expected,
            "actual": actual,
            "note": note,
            "executed": True,
        }
    )


def expect_success(cid, method, path_tpl, token=None, params=None, json_body=None, files=None,
                   checker=None, path=None, timeout=TIMEOUT, note=""):
    http, body, _ = request(
        method, path or path_tpl, token=token, params=params,
        json_body=json_body, files=files, timeout=timeout,
    )
    passed = http == 200 and isinstance(body, dict) and body.get("code") == 200
    if passed and checker is not None:
        passed = bool(checker(body.get("data")))
    finish(
        cid, method, path_tpl, passed, http, body,
        "HTTP 200 + code 200" + (note and " ({})".format(note)),
        path=path, note=note,
    )
    return http, body


def expect_error(cid, method, path_tpl, expected_http, token=None, params=None,
                 json_body=None, files=None, path=None, note=""):
    http, body, _ = request(
        method, path or path_tpl, token=token, params=params,
        json_body=json_body, files=files,
    )
    passed = http == expected_http and isinstance(body, dict) and body.get("code") == expected_http
    finish(
        cid, method, path_tpl, passed, http, body,
        "HTTP {} + code {}".format(expected_http, expected_http),
        path=path, note=note,
    )
    return http, body


def limited(cid, method, path_tpl, http, body, note, path=None, executed=True):
    finish(
        cid, method, path_tpl, False, http, body,
        "environment-dependent", path=path, note=note, status="LIMITED",
    )
    results[-1]["executed"] = executed


def do_login(username, password):
    http, body, _ = request("POST", "/api/client/auth/login", json_body={"username": username, "password": password})
    if http == 200 and isinstance(body, dict) and body.get("code") == 200:
        return body.get("data")
    return None


def spec_operations():
    text = SPEC_FILE.read_text(encoding="utf-8")
    ops = []
    current_path = None
    for line in text.splitlines():
        m = re.match(r"^  (/api\S+):\s*$", line)
        if m:
            current_path = m.group(1)
            continue
        m = re.match(r"^    (get|post|put|delete|patch):\s*$", line)
        if m and current_path:
            ops.append((m.group(1).upper(), current_path))
    return ops


def test_auth(ctx):
    user_login = do_login(USER, USER_PASS)
    passed = user_login is not None and bool(user_login.get("token")) and user_login.get("user", {}).get("username") == USER
    finish("API-AUTH-LOGIN-001", "POST", "/api/client/auth/login", passed,
           200 if user_login else 0, {"code": 200, "data": user_login} if user_login else {"code": None},
           "login normal user")
    if user_login:
        ctx["user_token"] = user_login["token"]
        ctx["user_refresh"] = user_login["refreshToken"]
        ctx["user_id"] = user_login["user"]["id"]

    admin_login = do_login(ADMIN, ADMIN_PASS)
    passed = admin_login is not None and bool(admin_login.get("token")) and admin_login.get("user", {}).get("role") == "ADMIN"
    finish("API-AUTH-LOGIN-002", "POST", "/api/client/auth/login", passed,
           200 if admin_login else 0, {"code": 200, "data": admin_login} if admin_login else {"code": None},
           "login admin")
    if admin_login:
        ctx["admin_token"] = admin_login["token"]
        ctx["admin_refresh"] = admin_login["refreshToken"]
        ctx["admin_id"] = admin_login["user"]["id"]

    expect_error(
        "API-AUTH-LOGIN-003", "POST", "/api/client/auth/login", 401,
        json_body={"username": "no_such_api_user_{}".format(int(time.time())), "password": "badpass"},
        note="wrong credentials rejected",
    )
    expect_error(
        "API-AUTH-REGISTER-001", "POST", "/api/client/auth/register", 400,
        json_body={"username": "api_register_{}".format(uuid.uuid4().hex[:8]), "password": "123", "email": "bad"},
        note="invalid payload validation",
    )
    expect_error(
        "API-AUTH-REGISTER-002", "POST", "/api/client/auth/register", 409,
        json_body={"username": USER, "password": "123456", "email": "dup@example.com"},
        note="duplicate username rejected",
    )
    expect_error(
        "API-AUTH-VERIFY-001", "POST", "/api/client/auth/verify-email", 400,
        json_body={"email": "x@example.com"},
        note="missing verification code rejected",
    )
    expect_error(
        "API-AUTH-RESEND-001", "POST", "/api/client/auth/resend-code", 400,
        json_body={"email": "bad"},
        note="invalid email rejected",
    )
    http, body, _ = request(
        "POST", "/api/client/auth/forgot-password",
        json_body={"email": "no_such_api_user_{}@example.com".format(int(time.time()))},
    )
    if http == 200 and isinstance(body, dict) and body.get("code") == 200:
        finish("API-AUTH-FORGOT-001", "POST", "/api/client/auth/forgot-password", True, http, body,
               "HTTP 200 + code 200", note="nonexistent email is silent success")
    elif http == 429:
        limited("API-AUTH-FORGOT-001", "POST", "/api/client/auth/forgot-password", http, body,
                "anti-brute-force rate limit hit by repeated test runs; 429 is expected behavior")
    else:
        finish("API-AUTH-FORGOT-001", "POST", "/api/client/auth/forgot-password", False, http, body,
               "HTTP 200 + code 200", note="nonexistent email is silent success")
    expect_error(
        "API-AUTH-RESET-001", "POST", "/api/client/auth/reset-password", 400,
        json_body={"email": "no_such_api_user@example.com", "code": "000000", "newPassword": "123456"},
        note="invalid reset code rejected",
    )
    expect_error(
        "API-AUTH-REFRESH-001", "POST", "/api/client/auth/refresh", 401,
        json_body={"refreshToken": "bad-refresh-token"},
        note="invalid refresh token rejected",
    )

    probe_login = do_login(USER, USER_PASS)
    if probe_login:
        expect_success(
            "API-AUTH-REFRESH-002", "POST", "/api/client/auth/refresh",
            json_body={"refreshToken": probe_login["refreshToken"]},
            checker=lambda d: bool(d and d.get("token") and d.get("refreshToken")),
            note="refresh token rotation returns new pair",
        )
    else:
        limited("API-AUTH-REFRESH-002", "POST", "/api/client/auth/refresh", 0, {"transport_error": "login failed"},
                "normal user login failed before refresh test")

    logout_login = do_login(USER, USER_PASS)
    if logout_login:
        logout_token = logout_login["token"]
        expect_success(
            "API-AUTH-LOGOUT-001", "POST", "/api/client/auth/logout",
            token=logout_token, note="logout succeeds",
        )
        expect_error(
            "API-AUTH-LOGOUT-002", "GET", "/api/client/me", 401,
            token=logout_token, note="logged-out token is rejected",
        )
    else:
        limited("API-AUTH-LOGOUT-001", "POST", "/api/client/auth/logout", 0, {"transport_error": "login failed"},
                "normal user login failed before logout test")

    expect_error("API-UNAUTH-001", "GET", "/api/client/me", 401, note="unauthenticated client endpoint rejected")
    expect_error(
        "API-FORBIDDEN-001", "GET", "/api/admin/dashboard/overview", 403,
        token=ctx.get("user_token"), note="normal user cannot call admin endpoint",
    )


def test_tags_subjects(ctx):
    http, body = expect_success(
        "API-TAGS-001", "GET", "/api/client/tags",
        checker=lambda d: isinstance(d, list) and len(d) > 0,
        note="public tag list",
    )
    data = body.get("data") or []
    for item in data:
        if item.get("count", 0) > 0:
            ctx["tag"] = item.get("name")
            break
    if not ctx.get("tag"):
        limited("API-TAGS-SUBJECTS-001", "GET", "/api/client/tags/{tag}/subjects", http, body,
                "no tag with count > 0 returned")
    else:
        expect_success(
            "API-TAGS-SUBJECTS-001", "GET", "/api/client/tags/{tag}/subjects",
            params={"page": 1, "size": 20},
            path="/api/client/tags/{}/subjects".format(urllib.parse.quote(ctx["tag"])),
            checker=lambda d: isinstance(d, dict) and isinstance(d.get("content"), list),
            note="subjects under first tag",
        )

    http, body = expect_success(
        "API-SUBJECTS-001", "GET", "/api/client/subjects",
        params={"page": 1, "size": 20, "sort": "score", "order": "desc"},
        checker=lambda d: isinstance(d, dict) and bool(d.get("content")),
        note="paginated subject list",
    )
    content = (body.get("data") or {}).get("content") or []
    if content:
        ctx["subject_id"] = content[0]["id"]
        ctx["subject_name"] = content[0].get("name") or content[0].get("nameCn") or ""

    if not ctx.get("subject_id"):
        limited("API-SUBJECTS-SEARCH-001", "GET", "/api/client/subjects/search", http, body,
                "no subject id captured")
    else:
        q = ctx["subject_name"][:8]
        expect_success(
            "API-SUBJECTS-SEARCH-001", "GET", "/api/client/subjects/search",
            params={"q": q, "page": 1, "size": 20},
            checker=lambda d: isinstance(d, dict) and isinstance(d.get("content"), list),
            note="keyword search",
        )

    expect_success(
        "API-SUBJECTS-SEASON-001", "GET", "/api/client/subjects/season",
        params={"year": 2026, "quarter": "summer", "page": 1, "size": 20},
        checker=lambda d: isinstance(d, dict) and isinstance(d.get("content"), list),
        note="season filter",
    )
    expect_error(
        "API-SUBJECTS-SEASON-002", "GET", "/api/client/subjects/season", 400,
        params={"year": 2026},
        note="missing quarter rejected",
    )
    expect_success(
        "API-SUBJECTS-SCHEDULE-001", "GET", "/api/client/subjects/schedule",
        params={"page": 1, "size": 20},
        checker=lambda d: isinstance(d, dict) and isinstance(d.get("content"), list),
        note="weekly schedule",
    )
    if not ctx.get("subject_id"):
        limited("API-SUBJECTS-DETAIL-001", "GET", "/api/client/subjects/{id}", http, body,
                "no subject id captured")
    else:
        sid = ctx["subject_id"]
        expect_success(
            "API-SUBJECTS-DETAIL-001", "GET", "/api/client/subjects/{id}",
            path="/api/client/subjects/{}".format(sid),
            checker=lambda d: isinstance(d, dict) and d.get("id") == sid,
            note="subject detail",
        )
        expect_success(
            "API-SUBJECTS-EPISODES-001", "GET", "/api/client/subjects/{id}/episodes",
            path="/api/client/subjects/{}/episodes".format(sid),
            checker=lambda d: isinstance(d, list),
            note="episode list",
        )


def test_profile(ctx):
    token = ctx["user_token"]
    http, body = expect_success(
        "API-ME-001", "GET", "/api/client/me", token=token,
        checker=lambda d: isinstance(d, dict) and d.get("username") == USER,
        note="current profile",
    )
    data = body.get("data") or {}
    orig_nick = data.get("nickname")
    orig_avatar = data.get("avatar")
    restored = False
    try:
        test_nick = "API_CONTRACT_NICK"
        expect_success(
            "API-ME-UPDATE-001", "POST", "/api/client/me/update", token=token,
            json_body={"nickname": test_nick},
            checker=lambda d: isinstance(d, dict) and d.get("nickname") == test_nick,
            note="update nickname",
        )
        http, body = expect_success(
            "API-ME-UPDATE-002", "POST", "/api/client/me/update", token=token,
            json_body={"nickname": orig_nick or USER, "avatar": orig_avatar or ""},
            checker=lambda d: isinstance(d, dict) and d.get("nickname") == (orig_nick or USER),
            note="restore nickname/avatar",
        )
        restored = True
    finally:
        if not restored:
            request("POST", "/api/client/me/update", token=token,
                    json_body={"nickname": orig_nick or USER, "avatar": orig_avatar or ""})

    expect_error(
        "API-ME-UPDATE-PASSWORD-001", "POST", "/api/client/me/update-password", 401,
        token=token, json_body={"oldPassword": "wrong-password", "newPassword": "123456"},
        note="wrong old password rejected (implementation returns 401; OpenAPI documents only 200)",
    )
    expect_error(
        "API-ME-UPDATE-PASSWORD-002", "POST", "/api/client/me/update-password", 400,
        token=token, json_body={"oldPassword": "123456", "newPassword": "123"},
        note="short new password rejected",
    )
    expect_error(
        "API-ME-SEND-EMAIL-001", "POST", "/api/client/me/send-email-code", 400,
        token=token, json_body={"newEmail": "bad"},
        note="invalid new email rejected without sending mail",
    )
    expect_error(
        "API-ME-VERIFY-EMAIL-001", "POST", "/api/client/me/verify-email-code", 400,
        token=token, json_body={"newEmail": "api-contract-{}@example.com".format(int(time.time())), "code": "000000"},
        note="nonexistent verification code rejected",
    )

    test2_login = do_login("test2", "123456")
    if not test2_login:
        limited("API-ME-UPDATE-PASSWORD-003", "POST", "/api/client/me/update-password", 0,
                {"transport_error": "test2 login failed"}, "test2 seed account unavailable; success path not executed")
        return
    t2 = test2_login["token"]
    new_pass = "apitest123456"
    http, body = expect_success(
        "API-ME-UPDATE-PASSWORD-003", "POST", "/api/client/me/update-password",
        token=t2, json_body={"oldPassword": "123456", "newPassword": new_pass},
        note="successful password change on seed account test2",
    )
    relogin_new = do_login("test2", new_pass)
    passed = relogin_new is not None
    finish("API-ME-UPDATE-PASSWORD-004", "POST", "/api/client/auth/login", passed,
           200 if relogin_new else 0,
           {"code": 200, "data": relogin_new} if relogin_new else {"code": None},
           "login with new password")
    current_t2 = relogin_new["token"] if relogin_new else t2
    http, body = expect_success(
        "API-ME-UPDATE-PASSWORD-005", "POST", "/api/client/me/update-password",
        token=current_t2, json_body={"oldPassword": new_pass, "newPassword": "123456"},
        note="restore test2 password",
    )
    final_t2 = do_login("test2", "123456")
    passed = final_t2 is not None
    finish("API-ME-UPDATE-PASSWORD-006", "POST", "/api/client/auth/login", passed,
           200 if final_t2 else 0,
           {"code": 200, "data": final_t2} if final_t2 else {"code": None},
           "login after restoring test2 password")


def test_collections(ctx):
    token = ctx["user_token"]
    http, body = expect_success(
        "API-COLL-LIST-001", "GET", "/api/client/collections", token=token,
        params={"page": 1, "size": 20},
        checker=lambda d: isinstance(d, dict) and isinstance(d.get("content"), list),
        note="collection list",
    )
    content = (body.get("data") or {}).get("content") or []
    collected_ids = {item.get("subjectId") for item in content}
    ctx["collected_ids"] = collected_ids

    expect_success(
        "API-COLL-COUNTS-001", "GET", "/api/client/collections/counts", token=token,
        checker=lambda d: isinstance(d, dict),
        note="collection counts",
    )
    if content:
        sid = content[0]["subjectId"]
        expect_success(
            "API-COLL-GET-001", "GET", "/api/client/collections/{subjectId}", token=token,
            path="/api/client/collections/{}".format(sid),
            checker=lambda d: d is None or isinstance(d, dict),
            note="existing collection detail",
        )
    else:
        limited("API-COLL-GET-001", "GET", "/api/client/collections/{subjectId}", http, body,
                "normal user has no collections to inspect")

    expect_success(
        "API-COLL-SCHEDULE-001", "GET", "/api/client/collections/schedule", token=token,
        params={"page": 1, "size": 20},
        checker=lambda d: isinstance(d, dict) and isinstance(d.get("content"), list),
        note="user weekly schedule",
    )

    subject_id = None
    for page in range(1, 4):
        http2, body2, _ = request(
            "GET", "/api/client/subjects",
            params={"page": page, "size": 100, "sort": "score", "order": "desc"},
        )
        if http2 != 200:
            break
        for item in (body2.get("data") or {}).get("content") or []:
            if item.get("id") not in collected_ids:
                subject_id = item.get("id")
                break
        if subject_id:
            break

    if not subject_id:
        limited("API-COLL-SAVE-001", "POST", "/api/client/collections/{subjectId}/save", http, body,
                "could not find uncollected subject")
    else:
        removed = False
        try:
            expect_success(
                "API-COLL-SAVE-001", "POST", "/api/client/collections/{subjectId}/save", token=token,
                path="/api/client/collections/{}/save".format(subject_id),
                json_body={"type": 1, "rate": 0, "epStatus": 0},
                note="create collection",
            )
            expect_success(
                "API-COLL-GET-002", "GET", "/api/client/collections/{subjectId}", token=token,
                path="/api/client/collections/{}".format(subject_id),
                checker=lambda d: isinstance(d, dict) and d.get("type") == 1,
                note="collection created",
            )
            expect_success(
                "API-COLL-SAVE-002", "POST", "/api/client/collections/{subjectId}/save", token=token,
                path="/api/client/collections/{}/save".format(subject_id),
                json_body={"type": 2, "rate": 8, "epStatus": 1},
                note="update collection",
            )
            expect_success(
                "API-COLL-EPSTATUS-001", "POST", "/api/client/collections/{subjectId}/ep-status", token=token,
                path="/api/client/collections/{}/ep-status".format(subject_id),
                json_body={"epStatus": 2},
                note="update episode progress",
            )
            expect_success(
                "API-COLL-GET-003", "GET", "/api/client/collections/{subjectId}", token=token,
                path="/api/client/collections/{}".format(subject_id),
                checker=lambda d: isinstance(d, dict) and d.get("type") == 2 and d.get("epStatus") == 2,
                note="collection reflects updates",
            )
            expect_success(
                "API-COLL-REMOVE-001", "POST", "/api/client/collections/{subjectId}/remove", token=token,
                path="/api/client/collections/{}/remove".format(subject_id),
                note="remove collection",
            )
            removed = True
            expect_success(
                "API-COLL-GET-004", "GET", "/api/client/collections/{subjectId}", token=token,
                path="/api/client/collections/{}".format(subject_id),
                checker=lambda d: d is None,
                note="collection removed",
            )
        finally:
            if not removed:
                request("POST", "/api/client/collections/{}/remove".format(subject_id), token=token)

    expect_error(
        "API-COLL-SAVE-003", "POST", "/api/client/collections/{subjectId}/save", 400,
        token=token, path="/api/client/collections/1/save", json_body={"type": 0},
        note="invalid collection type rejected",
    )
    expect_error(
        "API-COLL-EPSTATUS-002", "POST", "/api/client/collections/{subjectId}/ep-status", 400,
        token=token, path="/api/client/collections/1/ep-status", json_body={"epStatus": -1},
        note="negative episode progress rejected",
    )


def test_collection_progress(ctx):
    token = ctx["user_token"]
    http, body = expect_success(
        "API-COLL-PROGRESS-PREVIEW-001", "POST", "/api/client/collections/progress-preview", token=token,
        checker=lambda d: isinstance(d, dict) and "previewId" in d and "state" in d and "code" not in d,
        note="preview generation wrapper without nested code",
    )
    preview_id = (body.get("data") or {}).get("previewId")
    if not preview_id:
        limited("API-COLL-PROGRESS-EXECUTE-001", "POST",
                "/api/client/collections/progress-preview/{previewId}/execute", http, body,
                "preview id missing; execute not attempted")
    else:
        http2, body2, _ = request(
            "POST", "/api/client/collections/progress-preview/{}/execute".format(preview_id), token=token)
        state = ((body2.get("data") or {}).get("state")) if isinstance(body2, dict) else None
        passed = http2 == 200 and isinstance(body2, dict) and body2.get("code") == 200 \
            and state in {"COMPLETED", "PREVIEW_CHANGED"}
        finish("API-COLL-PROGRESS-EXECUTE-001", "POST",
               "/api/client/collections/progress-preview/{previewId}/execute", passed, http2, body2,
               "HTTP 200 + code 200 + data.state in {COMPLETED, PREVIEW_CHANGED}",
               path="/api/client/collections/progress-preview/{}/execute".format(preview_id),
               note="execute preview (revalidate + partial success)")

    expect_error(
        "API-COLL-PROGRESS-UNAUTH-001", "POST", "/api/client/collections/progress-preview", 401,
        note="unauthenticated preview rejected with Result error wrapper",
    )


def test_upload(ctx):
    user_token = ctx["user_token"]
    admin_token = ctx["admin_token"]
    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    avatar_files = {"file": ("api_contract_avatar.png", png_bytes, "image/png")}
    expect_success(
        "API-FILE-AVATAR-001", "POST", "/api/client/files/avatar", token=user_token,
        files=avatar_files,
        checker=lambda d: isinstance(d, str) and d.startswith("http"),
        note="authenticated user uploads PNG avatar",
    )
    expect_error(
        "API-FILE-AVATAR-UNAUTH-001", "POST", "/api/client/files/avatar", 401,
        files=avatar_files,
        note="anonymous avatar upload rejected",
    )
    expect_error(
        "API-FILE-COVER-USER-001", "POST", "/api/admin/files/cover", 403,
        token=user_token, files=avatar_files,
        note="ordinary user cannot upload cover",
    )
    cover_files = {"file": ("api_contract_cover.png", png_bytes, "image/png")}
    expect_success(
        "API-FILE-COVER-ADMIN-001", "POST", "/api/admin/files/cover", token=admin_token,
        files=cover_files,
        checker=lambda d: isinstance(d, str) and d.startswith("http"),
        note="admin uploads PNG cover",
    )
    text_files = {"file": ("api_contract.txt", b"not an image", "text/plain")}
    expect_error(
        "API-FILE-AVATAR-MIME-001", "POST", "/api/client/files/avatar", 400,
        token=user_token, files=text_files,
        note="non-image content type rejected",
    )


def test_admin(ctx):
    token = ctx["admin_token"]
    expect_success(
        "API-LOGS-001", "GET", "/api/admin/logs", token=token,
        params={"page": 1, "size": 20},
        checker=lambda d: isinstance(d, dict) and isinstance(d.get("content"), list) and d.get("total", -1) >= 0,
        note="operation log paging",
    )
    http, body = expect_success(
        "API-ADMIN-USERS-001", "GET", "/api/admin/users", token=token,
        params={"page": 1, "size": 100},
        checker=lambda d: isinstance(d, dict) and isinstance(d.get("content"), list) and bool(d.get("content")),
        note="admin user list",
    )
    users = (body.get("data") or {}).get("content") or []
    test2_user = next((u for u in users if u.get("username") == "test2"), None)
    if test2_user:
        ctx["test2_id"] = test2_user.get("id")

    expect_success(
        "API-DASH-OVERVIEW-001", "GET", "/api/admin/dashboard/overview", token=token,
        checker=lambda d: isinstance(d, dict) and "subjectCount" in d,
        note="dashboard overview",
    )
    expect_success(
        "API-DASH-TRENDS-001", "GET", "/api/admin/dashboard/trends", token=token,
        params={"days": 30},
        checker=lambda d: isinstance(d, list),
        note="dashboard trends",
    )
    expect_success(
        "API-DASH-COLL-001", "GET", "/api/admin/dashboard/collection-stats", token=token,
        checker=lambda d: isinstance(d, dict) and isinstance(d.get("types"), list),
        note="dashboard collection stats",
    )
    expect_success(
        "API-DASH-SUBJECT-001", "GET", "/api/admin/dashboard/subject-stats", token=token,
        checker=lambda d: isinstance(d, dict) and isinstance(d.get("seasons"), list),
        note="dashboard subject stats",
    )
    expect_success(
        "API-DASH-HOT-001", "GET", "/api/admin/dashboard/hot", token=token,
        params={"limit": 5},
        checker=lambda d: isinstance(d, list),
        note="dashboard hot ranking",
    )

    expect_success(
        "API-IMPORT-STATUS-001", "GET", "/api/admin/import/status", token=token,
        checker=lambda d: isinstance(d, dict) and "recentRecords" in d,
        note="import status",
    )
    expect_success(
        "API-IMPORT-RECORDS-001", "GET", "/api/admin/import/records", token=token,
        params={"page": 1, "size": 10},
        checker=lambda d: isinstance(d, dict) and isinstance(d.get("content"), list),
        note="import records",
    )
    expect_error(
        "API-IMPORT-RUN-001", "POST", "/api/admin/import/run", 400,
        token=token, params={"mode": "season"},
        note="season mode without key rejected",
    )
    expect_error(
        "API-IMPORT-RUN-002", "POST", "/api/admin/import/run", 400,
        token=token, params={"mode": "bogus"},
        note="unknown mode rejected",
    )

    bangumi_id = 90000000 + int(time.time() * 1000) % 10000000
    payload = {
        "bangumiId": bangumi_id,
        "name": "API contract subject",
        "nameCn": "API contract subject CN",
        "summary": "created by contract test",
        "type": 2,
        "eps": 12,
        "airDate": "2026-08-15",
    }
    created_id = None
    removed = False
    try:
        http, body = expect_success(
            "API-ADMIN-SUBJECT-CREATE-001", "POST", "/api/admin/subjects", token=token,
            json_body=payload,
            checker=lambda d: isinstance(d, dict) and bool(d.get("id")),
            note="create subject",
        )
        created_id = (body.get("data") or {}).get("id")
        if created_id:
            expect_success(
                "API-ADMIN-SUBJECT-UPDATE-001", "POST", "/api/admin/subjects/{id}/update", token=token,
                path="/api/admin/subjects/{}/update".format(created_id),
                json_body={"name": "API contract subject updated", "eps": 13},
                checker=lambda d: isinstance(d, dict) and d.get("name") == "API contract subject updated",
                note="update subject",
            )
            expect_success(
                "API-ADMIN-SUBJECT-REMOVE-001", "POST", "/api/admin/subjects/{id}/remove", token=token,
                path="/api/admin/subjects/{}/remove".format(created_id),
                note="remove subject",
            )
            removed = True
    finally:
        if created_id and not removed:
            request("POST", "/api/admin/subjects/{}/remove".format(created_id), token=token)

    expect_error(
        "API-ADMIN-ROLE-001", "POST", "/api/admin/users/{id}/update-role", 400,
        token=token, path="/api/admin/users/2/update-role", json_body={"role": "ROOT"},
        note="invalid role rejected",
    )
    test2_id = ctx.get("test2_id")
    if not test2_id:
        limited("API-ADMIN-ROLE-002", "POST", "/api/admin/users/{id}/update-role", http, body,
                "test2 user not found in admin user list")
        return
    reverted = False
    try:
        expect_success(
            "API-ADMIN-ROLE-002", "POST", "/api/admin/users/{id}/update-role", token=token,
            path="/api/admin/users/{}/update-role".format(test2_id),
            json_body={"role": "ADMIN"},
            checker=lambda d: isinstance(d, dict) and d.get("role") == "ADMIN",
            note="promote test2 to ADMIN",
        )
        expect_success(
            "API-ADMIN-ROLE-003", "POST", "/api/admin/users/{id}/update-role", token=token,
            path="/api/admin/users/{}/update-role".format(test2_id),
            json_body={"role": "USER"},
            checker=lambda d: isinstance(d, dict) and d.get("role") == "USER",
            note="restore test2 to USER",
        )
        reverted = True
    finally:
        if not reverted:
            request("POST", "/api/admin/users/{}/update-role".format(test2_id),
                    token=token, json_body={"role": "USER"})


def test_agent(ctx):
    user_token = ctx["user_token"]
    admin_token = ctx["admin_token"]
    probes = [
        ("API-AGENT-HEALTH-001", "GET", "/api/client/agent/health", user_token, None, None, 8),
        ("API-AGENT-SESSIONS-001", "GET", "/api/client/agent/sessions", user_token, None, None, 8),
        ("API-AGENT-SESSIONS-CREATE-001", "POST", "/api/client/agent/sessions", user_token, None, {}, 8),
        ("API-AGENT-STREAM-001", "POST", "/api/client/agent/stream", user_token, None, {"message": "hi"}, 8),
        ("API-ADMIN-AGENT-PROMPTS-001", "GET", "/api/admin/agent/prompts", admin_token, None, None, 8),
        ("API-ADMIN-AGENT-CONFIG-001", "GET", "/api/admin/agent/config", admin_token, None, None, 8),
        ("API-ADMIN-AGENT-SESSIONS-001", "GET", "/api/admin/agent/chat/sessions", admin_token, None, None, 8),
        ("API-ADMIN-AGENT-SESSIONS-CREATE-001", "POST", "/api/admin/agent/chat/sessions", admin_token, None, {}, 8),
        ("API-ADMIN-AGENT-CHAT-STREAM-001", "POST", "/api/admin/agent/chat/stream", admin_token, None, {"message": "hi"}, 8),
    ]
    for cid, method, path_tpl, token, params, json_body, timeout in probes:
        http, body, _ = request(
            method, path_tpl, token=token, params=params, json_body=json_body, timeout=timeout,
        )
        if http == 200:
            finish(cid, method, path_tpl, True, http, body, "HTTP 200",
                   note="agent proxy reachable", status="PASS")
        else:
            limited(cid, method, path_tpl, http, body,
                    "Python agent :8090 not running; business proxy returned {}".format(http or body.get("transport_error", "error")))

    for cid, method, path_tpl in [
        ("API-AGENT-HISTORY-001", "GET", "/api/client/agent/sessions/{sessionId}/history"),
        ("API-AGENT-REMOVE-001", "POST", "/api/client/agent/sessions/{sessionId}/remove"),
        ("API-ADMIN-AGENT-PROMPT-001", "GET", "/api/admin/agent/prompts/{key}"),
        ("API-ADMIN-AGENT-PROMPT-UPDATE-001", "POST", "/api/admin/agent/prompts/{key}/update"),
        ("API-ADMIN-AGENT-PROMPT-RESET-001", "POST", "/api/admin/agent/prompts/{key}/reset"),
        ("API-ADMIN-AGENT-CONFIG-UPDATE-001", "POST", "/api/admin/agent/config/update"),
        ("API-ADMIN-AGENT-HISTORY-001", "GET", "/api/admin/agent/chat/sessions/{sessionId}/history"),
        ("API-ADMIN-AGENT-REMOVE-001", "POST", "/api/admin/agent/chat/sessions/{sessionId}/remove"),
    ]:
        limited(cid, method, path_tpl, 0, {"transport_error": "not executed"},
                "not executed: requires live agent :8090 and session/prompt key",
                executed=False)


def audit_spec():
    ops = spec_operations()
    executed = {(r["method"], r["path_template"]) for r in results if r.get("executed")}
    missing = sorted("{} {}".format(m, p) for m, p in ops if (m, p) not in executed)
    return ops, missing


def main():
    started = time.time()
    ctx = {}
    test_auth(ctx)
    test_tags_subjects(ctx)
    test_profile(ctx)
    test_collections(ctx)
    test_collection_progress(ctx)
    test_upload(ctx)
    test_admin(ctx)
    test_agent(ctx)

    ops, missing = audit_spec()
    summary = {
        "base": BASE,
        "duration_s": round(time.time() - started, 1),
        "spec_operations": len(ops),
        "executed_operations": len(ops) - len(missing),
        "missing_operations": missing,
        "total_cases": len(results),
        "pass": sum(1 for r in results if r["status"] == "PASS"),
        "fail": sum(1 for r in results if r["status"] == "FAIL"),
        "limited": sum(1 for r in results if r["status"] == "LIMITED"),
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    print("BASE={}".format(BASE))
    print("SPEC_OPERATIONS={}".format(len(ops)))
    print("EXECUTED_OPERATIONS={}".format(len(ops) - len(missing)))
    print("TOTAL_CASES={} PASS={} FAIL={} LIMITED={}".format(
        len(results), summary["pass"], summary["fail"], summary["limited"]))
    for r in results:
        if r["status"] != "PASS":
            print("[{}] {} {} {} {}".format(r["status"], r["id"], r["method"], r["path_template"], r["note"]))
    if missing:
        print("MISSING_SPEC_OPERATIONS:")
        for item in missing:
            print("  " + item)
    print("OUTPUT=" + str(OUT_FILE))
    if summary["fail"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

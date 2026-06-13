import hashlib
import hmac
import json
import mimetypes
import os
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, List, Optional


LOVART_DEFAULT_BASE_URL = "https://lgw.lovart.ai"
LOVART_PATH_PREFIX = "/v1/openapi"
LOVART_REASONING_MODE_DEFAULT = "fast"
LOVART_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) LovartAgentSkill/1.0"
LOVART_CDN_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.lovart.ai/",
}

LOVART_IMAGE_MODEL_CATALOG: List[Dict[str, Any]] = [
    {"id": "generate_image_midjourney", "name": "Midjourney", "kind": "image", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_image_gpt_image_1_5", "name": "GPT Image 1.5", "kind": "image", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_image_gpt_image_2", "name": "GPT Image 2", "kind": "image", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_image_gpt_image_2_low", "name": "GPT Image 2 low", "kind": "image", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_image_nano_banana", "name": "Nano Banana", "kind": "image", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_image_nano_banana_2", "name": "Nano Banana 2", "kind": "image", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_image_nano_banana_pro", "name": "Nano Banana Pro", "kind": "image", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_image_seedream_v4", "name": "Seedream 4", "kind": "image", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_image_seedream_v4_5", "name": "Seedream 4.5", "kind": "image", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_image_flux_2_max", "name": "Flux 2 Max", "kind": "image", "billing": "no_confirm", "cost": None, "cost_label": "no_confirm"},
    {"id": "generate_image_flux_2_pro", "name": "Flux 2 Pro", "kind": "image", "billing": "no_confirm", "cost": None, "cost_label": "no_confirm"},
    {"id": "generate_image_ideogram_v4", "name": "Ideogram v4", "kind": "image", "billing": "no_confirm", "cost": None, "cost_label": "no_confirm"},
    {"id": "generate_image_seedream_v5", "name": "Seedream 5", "kind": "image", "billing": "no_confirm", "cost": None, "cost_label": "no_confirm"},
    {"id": "generate_image_gpt_image_2_medium", "name": "GPT Image 2 medium", "kind": "image", "billing": "paid", "cost": 14, "cost_label": "14 credits"},
    {"id": "generate_image_gpt_image_2_high", "name": "GPT Image 2 high", "kind": "image", "billing": "paid", "cost": 50, "cost_label": "50 credits"},
    {"id": "generate_image_luma_uni_1", "name": "Luma Uni 1", "kind": "image", "billing": "paid", "cost": None, "cost_label": "pending"},
    {"id": "generate_image_luma_uni_1_max", "name": "Luma Uni 1 Max", "kind": "image", "billing": "paid", "cost": None, "cost_label": "pending"},
]

LOVART_VIDEO_MODEL_CATALOG: List[Dict[str, Any]] = [
    {"id": "generate_video_kling_v2_6", "name": "Kling 2.6", "kind": "video", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_video_kling_omni_v1", "name": "Kling O1", "kind": "video", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_video_wan_v2_6", "name": "Wan 2.6", "kind": "video", "billing": "free", "cost": None, "cost_label": "free"},
    {"id": "generate_video_veo3", "name": "Veo3", "kind": "video", "billing": "paid", "cost": 10, "cost_label": "10 credits"},
    {"id": "generate_video_veo3_1", "name": "Veo3.1", "kind": "video", "billing": "paid", "cost": 14, "cost_label": "14 credits"},
    {"id": "generate_video_veo3_1_fast", "name": "Veo3.1 Fast", "kind": "video", "billing": "paid", "cost": 14, "cost_label": "14 credits"},
    {"id": "generate_video_seedance_v2_0", "name": "Seedance v2", "kind": "video", "billing": "paid", "cost": 14, "cost_label": "14 credits"},
    {"id": "generate_video_seedance_v2_0_fast", "name": "Seedance v2 Fast", "kind": "video", "billing": "paid", "cost": None, "cost_label": "pending"},
    {"id": "generate_video_seedance_pro_v1_5", "name": "Seedance Pro 1.5", "kind": "video", "billing": "paid", "cost": 14, "cost_label": "14 credits"},
    {"id": "generate_video_kling_v3", "name": "Kling v3", "kind": "video", "billing": "paid", "cost": None, "cost_label": "pending"},
    {"id": "generate_video_kling_v3_omni", "name": "Kling v3 Omni", "kind": "video", "billing": "paid", "cost": None, "cost_label": "pending"},
    {"id": "generate_video_hailuo_v2_3", "name": "Hailuo v2.3", "kind": "video", "billing": "paid", "cost": 14, "cost_label": "14 credits"},
    {"id": "generate_video_vidu_q2", "name": "Vidu Q2", "kind": "video", "billing": "paid", "cost": 14, "cost_label": "14 credits"},
]

LOVART_MODEL_CATALOG: List[Dict[str, Any]] = [
    *LOVART_IMAGE_MODEL_CATALOG,
    *LOVART_VIDEO_MODEL_CATALOG,
]
LOVART_MODEL_META: Dict[str, Dict[str, Any]] = {item["id"]: dict(item) for item in LOVART_MODEL_CATALOG}
LOVART_IMAGE_MODEL_IDS = [item["id"] for item in LOVART_IMAGE_MODEL_CATALOG]
LOVART_VIDEO_MODEL_IDS = [item["id"] for item in LOVART_VIDEO_MODEL_CATALOG]

_SUBMIT_LOCK = threading.Lock()
_STATE_LOCK = threading.Lock()


class LovartError(Exception):
    def __init__(self, message: str, code: int = 0):
        self.message = message
        self.code = code
        super().__init__(message)


def _ssl_context():
    ctx = ssl.create_default_context()
    if os.environ.get("LOVART_INSECURE_SSL") == "1":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def lovart_access_key(explicit: str = "") -> str:
    return str(explicit or os.environ.get("LOVART_ACCESS_KEY") or "").strip()


def lovart_secret_key(explicit: str = "") -> str:
    return str(explicit or os.environ.get("LOVART_SECRET_KEY") or "").strip()


def lovart_base_url(explicit: str = "") -> str:
    return str(explicit or os.environ.get("LOVART_BASE_URL") or LOVART_DEFAULT_BASE_URL).strip().rstrip("/")


def lovart_reasoning_mode(explicit: str = "") -> str:
    value = str(explicit or os.environ.get("LOVART_REASONING_MODE") or LOVART_REASONING_MODE_DEFAULT).strip().lower()
    return value if value in {"fast", "thinking"} else LOVART_REASONING_MODE_DEFAULT


def ensure_lovart_credentials(access_key: str = "", secret_key: str = "") -> tuple[str, str]:
    ak = lovart_access_key(access_key)
    sk = lovart_secret_key(secret_key)
    if not ak or not sk:
        raise LovartError("Missing Lovart access key or secret key")
    return ak, sk


class LovartClient:
    def __init__(
        self,
        base_url: str = "",
        access_key: str = "",
        secret_key: str = "",
        timeout: int = 180,
        poll_interval: int = 3,
        path_prefix: str = LOVART_PATH_PREFIX,
    ):
        ak, sk = ensure_lovart_credentials(access_key, secret_key)
        self.base_url = lovart_base_url(base_url)
        self.access_key = ak
        self.secret_key = sk
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.prefix = path_prefix
        self._pending_confirmation: Dict[str, Any] = {}

    def _sign(self, method: str, path: str) -> Dict[str, str]:
        ts = str(int(time.time()))
        sig = hmac.new(
            self.secret_key.encode(),
            f"{method}\n{path}\n{ts}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return {
            "X-Access-Key": self.access_key,
            "X-Timestamp": ts,
            "X-Signature": sig,
            "X-Signed-Method": method,
            "X-Signed-Path": path,
        }

    def request(self, method: str, path: str, body: Any = None, params: Optional[Dict[str, Any]] = None, retries: Optional[int] = None) -> Any:
        if retries is None:
            retries = 3 if method == "GET" else 1
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        last_err = None
        idempotency_key = uuid.uuid4().hex if method == "POST" else None
        for attempt in range(retries):
            headers = self._sign(method, path)
            headers["Content-Type"] = "application/json"
            headers["User-Agent"] = LOVART_USER_AGENT
            if idempotency_key:
                headers["Idempotency-Key"] = idempotency_key
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout, context=_ssl_context()) as resp:
                    result = json.loads(resp.read().decode())
                    break
            except urllib.error.HTTPError as exc:
                err_body = exc.read().decode()
                if exc.code in (404, 429, 502, 503) and attempt < retries - 1:
                    last_err = exc
                    time.sleep(2 * (attempt + 1))
                    continue
                try:
                    raw = json.loads(err_body)
                    msg = raw.get("message") or raw.get("error") or str(exc)
                    details = raw.get("details") or ""
                    if details:
                        msg = f"{msg}: {details}"
                    raise LovartError(msg, exc.code)
                except (json.JSONDecodeError, KeyError):
                    raise LovartError(f"HTTP {exc.code}: {err_body}", exc.code)
            except (urllib.error.URLError, ssl.SSLError, ConnectionError, OSError) as exc:
                last_err = exc
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise LovartError(f"Connection failed after {retries} attempts: {exc}")
        else:
            raise LovartError(f"Connection failed: {last_err}")

        if isinstance(result, dict) and result.get("code", 0) != 0:
            raise LovartError(str(result.get("message") or "Unknown error"), int(result.get("code") or -1))
        return result.get("data", result) if isinstance(result, dict) else result

    def save_project(self, project_id: str = "", canvas: str = "", project_name: str = "", project_type: int = 3) -> Dict[str, Any]:
        body = {
            "project_id": project_id,
            "canvas": canvas,
            "project_cover_list": [],
            "pic_count": 0,
            "project_type": project_type,
        }
        if project_name:
            body["project_name"] = project_name
        return self.request("POST", f"{self.prefix}/project/save", body=body)

    def create_project(self, project_type: int = 3) -> str:
        result = self.save_project(project_type=project_type)
        return str(result.get("project_id") or "").strip()

    def validate_project(self, project_id: str) -> bool:
        if not project_id:
            return False
        try:
            result = self.request("GET", f"{self.prefix}/project/validate", params={"project_id": project_id})
            return bool(result.get("valid"))
        except LovartError:
            return False

    def set_mode(self, unlimited: bool) -> Dict[str, Any]:
        return self.request("POST", f"{self.prefix}/mode/set", body={"unlimited": bool(unlimited)})

    def query_mode(self) -> Dict[str, Any]:
        return self.request("POST", f"{self.prefix}/mode/query", body={})

    def confirm(self, thread_id: str) -> Dict[str, Any]:
        return self.request("POST", f"{self.prefix}/chat/confirm", body={"thread_id": thread_id})

    def upload_file(self, local_path: str) -> str:
        with open(local_path, "rb") as handle:
            file_data = handle.read()
        filename = os.path.basename(local_path)
        boundary = uuid.uuid4().hex
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
        path = f"{self.prefix}/file/upload"
        headers = self._sign("POST", path)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        headers["User-Agent"] = LOVART_USER_AGENT
        req = urllib.request.Request(f"{self.base_url}{path}", data=body, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=_ssl_context()) as resp:
                result = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            raise LovartError(f"Upload failed ({exc.code}): {exc.read().decode()}", exc.code)
        if isinstance(result, dict) and result.get("code", 0) != 0:
            raise LovartError(f"Upload failed: {result.get('message') or 'unknown error'}", int(result.get("code") or -1))
        url = (((result or {}).get("data") or {}).get("url") or "").strip()
        if not url:
            raise LovartError("Upload succeeded but did not return a URL")
        return url

    def send(
        self,
        prompt: str,
        project_id: str,
        attachments: Optional[List[str]] = None,
        include_tools: Optional[List[str]] = None,
        thread_id: str = "",
        mode: str = "",
    ) -> str:
        body: Dict[str, Any] = {"prompt": prompt, "project_id": project_id}
        if attachments:
            body["attachments"] = attachments
        if thread_id:
            body["thread_id"] = thread_id
        reasoning = lovart_reasoning_mode(mode)
        if reasoning:
            body["mode"] = reasoning
        if include_tools:
            body["tool_config"] = {"include_tools": include_tools}
        data = self.request("POST", f"{self.prefix}/chat", body=body)
        tid = str((data or {}).get("thread_id") or "").strip()
        if not tid:
            raise LovartError("Lovart chat did not return thread_id")
        return tid

    def status(self, thread_id: str) -> Dict[str, Any]:
        return self.request("GET", f"{self.prefix}/chat/status", params={"thread_id": thread_id})

    def result(self, thread_id: str) -> Dict[str, Any]:
        return self.request("GET", f"{self.prefix}/chat/result", params={"thread_id": thread_id})

    def poll(self, thread_id: str, timeout: Optional[int] = None) -> str:
        deadline = time.time() + (timeout or self.timeout)
        confirm_delay = 5
        poll_count = 0
        self._pending_confirmation = {}
        while time.time() < deadline:
            status_info = self.status(thread_id)
            status = str(status_info.get("status") or "running").lower()
            poll_count += 1
            if status == "abort":
                return "abort"
            if status == "done":
                time.sleep(confirm_delay)
                status2 = str(self.status(thread_id).get("status") or "running").lower()
                if status2 in {"done", "abort"}:
                    try:
                        result = self.result(thread_id)
                        pc = result.get("pending_confirmation")
                        if pc:
                            self._pending_confirmation = pc
                            return "pending_confirmation"
                    except Exception:
                        pass
                    return status2
            if poll_count >= 7 and status == "running" and poll_count % 3 == 0:
                try:
                    result = self.result(thread_id)
                    pc = result.get("pending_confirmation")
                    if pc:
                        self._pending_confirmation = pc
                        return "pending_confirmation"
                except Exception:
                    pass
            time.sleep(self.poll_interval)
        return "timeout"


def load_state(state_path: str) -> Dict[str, Any]:
    if not state_path or not os.path.exists(state_path):
        return {"project_id": "", "tasks": {}}
    try:
        with open(state_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        data = {}
    if "active_project" in data and "project_id" not in data:
        data["project_id"] = data.get("active_project") or ""
    data.setdefault("project_id", "")
    data.setdefault("tasks", {})
    return data


def save_state(state_path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    tmp = f"{state_path}.tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    os.replace(tmp, state_path)


def ensure_project(client: LovartClient, state_path: str) -> str:
    with _STATE_LOCK:
        state = load_state(state_path)
        project_id = str(state.get("project_id") or "").strip()
        if project_id and client.validate_project(project_id):
            return project_id
        project_id = client.create_project()
        if not project_id:
            raise LovartError("Lovart did not return project_id")
        state["project_id"] = project_id
        save_state(state_path, state)
        return project_id


def record_task(state_path: str, task_id: str, payload: Dict[str, Any]) -> None:
    if not state_path or not task_id:
        return
    with _STATE_LOCK:
        state = load_state(state_path)
        tasks = state.setdefault("tasks", {})
        current = tasks.get(task_id) or {}
        current.update(payload)
        current["updated_at"] = time.time()
        tasks[task_id] = current
        save_state(state_path, state)


def model_metadata(mode_data: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
    free_tools = set()
    if isinstance(mode_data, dict):
        raw = mode_data.get("unlimited_list") or []
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str):
                    free_tools.add(item)
                elif isinstance(item, dict):
                    value = item.get("id") or item.get("tool_name") or item.get("name")
                    if value:
                        free_tools.add(str(value))
    meta = {}
    for mid, item in LOVART_MODEL_META.items():
        enriched = dict(item)
        if mid in free_tools:
            enriched["billing"] = "free"
            enriched["cost_label"] = "free"
            enriched["unlimited_available"] = True
        else:
            enriched["unlimited_available"] = item.get("billing") == "free"
        meta[mid] = enriched
    return meta


def models_payload(mode_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    meta = model_metadata(mode_data)
    return {
        "total": len(LOVART_IMAGE_MODEL_IDS) + len(LOVART_VIDEO_MODEL_IDS),
        "protocol": "lovart",
        "image_models": LOVART_IMAGE_MODEL_IDS,
        "chat_models": [],
        "video_models": LOVART_VIDEO_MODEL_IDS,
        "all": [*LOVART_IMAGE_MODEL_IDS, *LOVART_VIDEO_MODEL_IDS],
        "model_metadata": meta,
        "raw": mode_data or {},
    }


def query_mode_with_keys(base_url: str = "", access_key: str = "", secret_key: str = "") -> Dict[str, Any]:
    return LovartClient(base_url=base_url, access_key=access_key, secret_key=secret_key, timeout=60).query_mode()


def set_mode_with_keys(unlimited: bool, base_url: str = "", access_key: str = "", secret_key: str = "") -> Dict[str, Any]:
    return LovartClient(base_url=base_url, access_key=access_key, secret_key=secret_key, timeout=60).set_mode(unlimited)


def upload_attachments(client: LovartClient, attachments: Optional[List[str]] = None) -> List[str]:
    uploaded = []
    for item in attachments or []:
        value = str(item or "").strip()
        if not value:
            continue
        if value.startswith("http://") or value.startswith("https://"):
            uploaded.append(value)
            continue
        if not os.path.exists(value):
            raise LovartError(f"Attachment does not exist: {value}")
        uploaded.append(client.upload_file(value))
    return uploaded


def submit_and_poll(
    *,
    prompt: str,
    model: str,
    kind: str,
    billing_unlimited: bool,
    state_path: str,
    task_id: str,
    attachments: Optional[List[str]] = None,
    timeout: int = 300,
    base_url: str = "",
    access_key: str = "",
    secret_key: str = "",
    reasoning_mode: str = "",
) -> Dict[str, Any]:
    client = LovartClient(base_url=base_url, access_key=access_key, secret_key=secret_key, timeout=max(60, timeout))
    project_id = ensure_project(client, state_path)
    uploaded_attachments = upload_attachments(client, attachments)
    with _SUBMIT_LOCK:
        client.set_mode(bool(billing_unlimited))
        thread_id = client.send(
            prompt=prompt,
            project_id=project_id,
            attachments=uploaded_attachments,
            include_tools=[model] if model else None,
            mode=reasoning_mode,
        )
    record_task(state_path, task_id, {
        "task_id": task_id,
        "thread_id": thread_id,
        "project_id": project_id,
        "kind": kind,
        "model": model,
        "billing_mode": "unlimited" if billing_unlimited else "fast",
        "billing_unlimited": bool(billing_unlimited),
        "status": "running",
    })
    status = client.poll(thread_id, timeout=timeout)
    if status == "pending_confirmation":
        result = {
            "thread_id": thread_id,
            "project_id": project_id,
            "final_status": "pending_confirmation",
            "pending_confirmation": client._pending_confirmation or {},
            "items": [],
        }
    else:
        result = client.result(thread_id)
        result["final_status"] = status
        result["project_id"] = project_id
        result["thread_id"] = thread_id
        mark_generation_success(result)
    return result


def confirm_and_poll(
    *,
    thread_id: str,
    state_path: str,
    task_id: str,
    timeout: int = 600,
    base_url: str = "",
    access_key: str = "",
    secret_key: str = "",
) -> Dict[str, Any]:
    client = LovartClient(base_url=base_url, access_key=access_key, secret_key=secret_key, timeout=max(60, timeout))
    client.confirm(thread_id)
    record_task(state_path, task_id, {"status": "running", "thread_id": thread_id})
    status = client.poll(thread_id, timeout=timeout)
    if status == "pending_confirmation":
        result = {
            "thread_id": thread_id,
            "final_status": "pending_confirmation",
            "pending_confirmation": client._pending_confirmation or {},
            "items": [],
        }
    else:
        result = client.result(thread_id)
        result["final_status"] = status
        result["thread_id"] = thread_id
        mark_generation_success(result)
    return result


def mark_generation_success(result: Dict[str, Any]) -> None:
    status = str(result.get("final_status") or "").lower()
    if status != "done":
        return
    has_artifact = any(item.get("artifacts") for item in result.get("items") or [] if isinstance(item, dict))
    result["generation_succeeded"] = bool(has_artifact)
    if not has_artifact:
        texts = [
            str(item.get("text") or "").strip()
            for item in result.get("items") or []
            if isinstance(item, dict) and item.get("text")
        ]
        result["warning"] = "Lovart thread ended without producing any artifact."
        if texts:
            result["agent_message"] = "\n\n".join(texts)


def extract_artifacts(result: Dict[str, Any], kind: str = "") -> List[Dict[str, str]]:
    artifacts = []
    seen = set()
    for item in result.get("items") or []:
        if not isinstance(item, dict):
            continue
        for artifact in item.get("artifacts") or []:
            if not isinstance(artifact, dict):
                continue
            url = str(artifact.get("content") or artifact.get("url") or "").strip()
            atype = str(artifact.get("type") or "").strip().lower() or "unknown"
            if not url or url in seen:
                continue
            if kind == "image" and atype == "video":
                continue
            if kind == "video" and atype not in {"video", "unknown"}:
                continue
            seen.add(url)
            artifacts.append({"type": atype, "url": url})
    return artifacts


def download_artifact(url: str, output_dir: str, prefix: str = "lovart") -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    clean_path = urllib.parse.urlparse(url).path
    ext = os.path.splitext(clean_path)[1].lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".webm", ".mov"}:
        ext = ".mp4" if "video" in prefix else ".png"
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:12]
    local_path = os.path.join(output_dir, f"{prefix}_{url_hash}{ext}")
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return {"url": url, "local_path": local_path, "new": False}
    req = urllib.request.Request(url, headers=LOVART_CDN_HEADERS)
    with urllib.request.urlopen(req, timeout=180, context=_ssl_context()) as resp:
        with open(local_path, "wb") as handle:
            handle.write(resp.read())
    return {"url": url, "local_path": local_path, "new": True}


def download_artifacts(result: Dict[str, Any], output_dir: str, kind: str = "", prefix: str = "lovart") -> List[Dict[str, Any]]:
    out = []
    for artifact in extract_artifacts(result, kind=kind):
        item = download_artifact(artifact["url"], output_dir, prefix=prefix)
        item["type"] = artifact["type"]
        out.append(item)
    return out


def pending_cost(model: str, pending_confirmation: Optional[Dict[str, Any]] = None) -> Any:
    pc = pending_confirmation or {}
    for key in ("estimated_cost", "estimatedCost", "cost", "credits"):
        if key in pc and pc.get(key) not in (None, ""):
            return pc.get(key)
    meta = LOVART_MODEL_META.get(str(model or ""))
    return meta.get("cost") if meta else None


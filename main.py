import time
import uuid
import hashlib
import requests
import asyncio
from pathlib import Path
from typing import Tuple, Optional

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp
from astrbot.core.utils.astrbot_path import get_astrbot_data_path


@register("strava_uploader", "xingmeng0721", "Strava 上传插件", "1.0.2")
class StravaUploaderPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        # 初始化数据存储目录
        self.data_dir = Path(get_astrbot_data_path()) / "plugin_data" / self.name
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化防重复记录集合和文件
        self.synced_keys = set()
        self.synced_txt_path = self.data_dir / "synced_records.txt"
        self._load_synced_records()

        # 伪装浏览器请求头
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # 启动后台自动同步任务
        self.sync_task = asyncio.create_task(self._auto_sync_loop())

    def _check_permission(self, event: AstrMessageEvent) -> bool:
        # 检查发送者是否在允许的名单中
        sender_id = str(event.get_sender_id())
        allowed_str = self.config.get("allowed_users", "")
        if not allowed_str:
            return True
        allowed = [u.strip() for u in str(allowed_str).split(",") if u.strip()]
        return not allowed or sender_id in allowed

    def _load_synced_records(self):
        # 启动时加载已经同步过的记录
        if self.synced_txt_path.exists():
            with open(self.synced_txt_path, "r", encoding="utf-8") as f:
                self.synced_keys = set(line.strip() for line in f if line.strip())
        else:
            self.synced_txt_path.touch()

    def mark_as_synced(self, file_key: str):
        # 将新同步的记录追加到文件和集合中
        if file_key not in self.synced_keys:
            self.synced_keys.add(file_key)
            with open(self.synced_txt_path, "a", encoding="utf-8") as f:
                f.write(f"{file_key}\n")

    def _md5(self, text: str) -> str:
        # MD5 加密工具函数
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _get_onelap_headers(
        self, account: str = None, password_md5: str = None, token: str = None
    ) -> dict:
        # 构造顽鹿运动 API 要求的签名请求头
        nonce = uuid.uuid4().hex
        timestamp = str(int(time.time()))
        key = "fe9f8382418fcdeb136461cac6acae7b"
        if account and password_md5:
            sign_str = f"account={account}&nonce={nonce}&password={password_md5}&timestamp={timestamp}&key={key}"
        else:
            sign_str = f"nonce={nonce}&timestamp={timestamp}&key={key}"
        sign = self._md5(sign_str)
        headers = {
            "nonce": nonce,
            "timestamp": timestamp,
            "sign": sign,
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = token
        return headers

    def get_strava_token(self) -> Optional[str]:
        # 获取或刷新 Strava Token
        c_id, c_secret, r_token = (
            self.config.get("client_id"),
            self.config.get("client_secret"),
            self.config.get("refresh_token"),
        )
        if not all([c_id, c_secret, r_token]):
            return None
        try:
            resp = requests.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": c_id,
                    "client_secret": c_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": r_token,
                },
                timeout=10,
            )
            data = resp.json()
            if resp.status_code == 200 and "access_token" in data:
                if data.get("refresh_token") and data["refresh_token"] != r_token:
                    self.config["refresh_token"] = data["refresh_token"]
                    self.config.save_config()
                return data["access_token"]
        except Exception as e:
            logger.error(f"Strava Token Error: {e}")
        return None

    def upload_to_strava(self, local_path: Path, file_name: str) -> Tuple[bool, str]:
        # 上传 FIT 文件到 Strava，并轮询获取处理结果
        token = self.get_strava_token()
        if not token:
            return False, "获取 Token 失败"

        headers = {"Authorization": f"Bearer {token}"}
        # 重复判定
        payload = {
            "data_type": "fit",
            "sport_type": "Ride",
            "external_id": file_name.replace(".fit", "").replace(".FIT", ""),
        }

        try:
            # 发起 POST 上传
            with open(local_path, "rb") as f:
                files = {"file": (file_name, f, "application/octet-stream")}
                post_resp = requests.post(
                    "https://www.strava.com/api/v3/uploads",
                    headers=headers,
                    data=payload,
                    files=files,
                    timeout=30,
                )

            if post_resp.status_code != 201:
                return False, f"POST 失败: {post_resp.text}"

            upload_id = post_resp.json().get("id_str")
            if not upload_id:
                return False, "未获取到 id_str"

            # 轮询 GET 状态
            poll_url = f"https://www.strava.com/api/v3/uploads/{upload_id}"
            for _ in range(20):
                time.sleep(2)
                poll_resp = requests.get(poll_url, headers=headers, timeout=10).json()

                # 检查错误
                error_msg = poll_resp.get("error")
                if error_msg:
                    if "duplicate" in error_msg.lower():
                        return True, "duplicate"  # 判定为已存在
                    return False, f"Strava错误: {error_msg}"

                # 检查成功状态
                if (
                    poll_resp.get("activity_id")
                    or poll_resp.get("status") == "Your activity is ready."
                ):
                    return True, "success"

                # 正在处理中则继续循环
                if "processed" in poll_resp.get("status", "").lower():
                    continue

            return False, "Strava 处理超时"
        except Exception as e:
            return False, f"上传异常: {str(e)}"

    def sync_onelap_to_strava(self) -> str:
        # 从顽鹿运动拉取记录并上传到 Strava
        account, password = (
            self.config.get("onelap_account"),
            self.config.get("onelap_password"),
        )
        sync_count = int(self.config.get("sync_count", 1))
        if not account or not password:
            return "未配置顽鹿账号。"

        try:
            session = requests.Session()
            md5_pwd = self._md5(password)
            login_req = session.post(
                "https://www.onelap.cn/api/login",
                json={"account": account, "password": md5_pwd},
                headers=self._get_onelap_headers(account, md5_pwd),
                timeout=15,
            )
            d = login_req.json().get("data")
            onelap_token = (
                (d[0].get("token") if isinstance(d, list) and d else d.get("token"))
                if d
                else None
            )
            if not onelap_token:
                return "顽鹿登录失败。"

            list_req = session.get(
                "https://u.onelap.cn/analysis/list",
                headers=self._get_onelap_headers(token=onelap_token),
                timeout=15,
            )
            activities = (
                list_req.json().get("data", {}).get("list", [])
                if isinstance(list_req.json().get("data"), dict)
                else list_req.json().get("data", [])
            )
            if not activities:
                return "无运动记录。"

            activities = activities[:sync_count]
            success, duplicate, fail, skipped = 0, 0, 0, 0

            for act in activities:
                f_key, f_url = act.get("fileKey"), act.get("durl")
                if f_key in self.synced_keys:
                    skipped += 1
                    continue
                if not f_key or not f_url:
                    continue

                local_path = self.data_dir / f"{f_key}.fit"
                try:
                    with session.post(
                        f_url, stream=True, headers={"User-Agent": self.user_agent}
                    ) as r:
                        with open(local_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)

                    if local_path.exists() and local_path.stat().st_size > 0:
                        status, reason = self.upload_to_strava(
                            local_path, f"{f_key}.fit"
                        )
                        if status:
                            self.mark_as_synced(f_key)
                            if reason == "success":
                                success += 1
                            else:
                                duplicate += 1
                        else:
                            fail += 1
                finally:
                    if local_path.exists():
                        local_path.unlink()

            return f"同步完成！\n获取记录：{len(activities)} 条\n新上传：{success}\nStrava重复：{duplicate}\n历史跳过：{skipped}\n失败：{fail}"
        except Exception as e:
            return f"错误: {str(e)}"

    async def _auto_sync_loop(self):
        # 自动同步的后台常驻任务
        await asyncio.sleep(20)
        while True:
            if self.config.get("auto_sync_enable", False):
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.sync_onelap_to_strava)
            await asyncio.sleep(
                max(int(self.config.get("auto_sync_interval", 6)) * 3600, 60)
            )

    """命令触发手动同步顽鹿记录到 Strava"""

    @filter.command("sync_onelap")
    async def cmd_sync_onelap(self, event: AstrMessageEvent):

        if not self._check_permission(event):
            yield event.plain_result("杂鱼权限不足")
            return

        yield event.plain_result("正在触发同步...")
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.sync_onelap_to_strava)
        yield event.plain_result(res)

    """自动拦截消息中的 FIT 文件并上传到 Strava"""

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def auto_intercept_file(self, event: AstrMessageEvent):
        for comp in event.message_obj.message:
            if isinstance(comp, Comp.File):
                f_name = getattr(comp, "name", "") or getattr(comp, "file_name", "")
                f_url = getattr(comp, "url", "")
                if f_name.lower().endswith(".fit") and f_url:
                    if not self._check_permission(event):
                        yield event.plain_result("杂鱼权限不足")
                        return
                    yield event.plain_result("识别到 FIT，同步至 Strava...")
                    local_path = self.data_dir / f_name

                    def process():
                        try:
                            with requests.get(f_url, stream=True, timeout=30) as r:
                                with open(local_path, "wb") as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        f.write(chunk)
                            return self.upload_to_strava(local_path, f_name)
                        finally:
                            if local_path.exists():
                                local_path.unlink()

                    loop = asyncio.get_running_loop()
                    status, reason = await loop.run_in_executor(None, process)
                    if status:
                        yield event.plain_result(
                            "上传成功！"
                            if reason == "success"
                            else "Strava 已存在相同记录。"
                        )
                    else:
                        yield event.plain_result(f"上传失败: {reason}")

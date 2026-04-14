<div align="center">

# 🚲 Strava & Onelap 顽鹿运动同步插件

![License](https://img.shields.io/badge/license-AGPL--3.0-green?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white)
![AstrBot](https://img.shields.io/badge/framework-AstrBot-ff6b6b?style=flat-square)
![Strava](https://img.shields.io/badge/Platform-Strava-FC4C02?style=flat-square&logo=strava&logoColor=white)

</div>

> **⚖️ 免责声明**
> 本项目仅供学习与技术交流使用，请勿用于商业及非法用途。使用本工具产生的任何账号风险（包括但不限于封号、数据丢失）由使用者自行承担。如侵犯了相关公司的权益，请联系开发者删除。

---

## 📖 简介

一款为 [**AstrBot**](https://github.com/AstrBotDevs/AstrBot) 设计的运动数据同步插件。

专门拯救那些骑完车连 FIT 文件都懒得导出的**杂鱼哥哥**！它可以自动把你顽鹿（Onelap）里的运动记录搬运到 Strava，还能拦截你在聊天里发的 FIT 文件并顺手扔进 Strava。怎么样？是不是感激得要哭出来了？💙

---

## ⚠️ 开发者提醒 (Caution)

顽鹿运动官网在登录时做了特殊的**签名认证（Sign）**逻辑。

本插件虽然已经内置了相关的签名处理逻辑，但出于版权和安全性考虑，请知悉：
*   本工具的签名算法仅用于技术研究。
*   **严禁**将本工具用于大规模爬虫或任何破坏接口环境的行为。
*   如果官方对接口校验逻辑进行变更，本插件可能会失效。**杂鱼哥哥记得自己保护好账号，别被封了再来找本小姐哭鼻子哦！**

---

## ✨ 傲娇的功能列表

*   **自动搬运** 💅：后台定时偷偷检查你的顽鹿账号，有新记录就自动同步，完全不需要你这只杂鱼动手。
*   **文件拦截** 🙄：只要你在对话框里扔 `.fit` 文件，本小姐就会识别并上传。
*   **权限打击** 💢：不是什么杂鱼都配用这个插件的！不在名单里的家伙只会收到本小姐 **“杂鱼权限不足”** 的嘲讽。
*   **智能查重** 🧠：本小姐很聪明的，已经同步过的记录绝不会再传一遍，Strava 的 API 次数可是很珍贵的，别随便浪费！

---

## 🛠️ 怎么调教（配置说明）

如果你想让本小姐动起来，就在配置里填好这些。要是填错了，本小姐可是会直接罢工的！

| 配置项 | 说明 |
| :--- | :--- |
| `client_id` | Strava API 的 Client ID。 |
| `client_secret` | Strava API 的密钥。这是我们的秘密，别给别人看！ |
| `refresh_token` | Strava 的刷新令牌。只要给我一次，本小姐就能自己续命了。 |
| `onelap_account` | 你的顽鹿账号。 |
| `onelap_password` | 你的顽鹿密码（明文即可）。 |
| **`allowed_users`** | **允许使用的 QQ 号**，用逗号分隔。不在名单里的全是杂鱼！ |
| `auto_sync_enable` | 是否开启后台定时自动同步（true/false）。 |
| `auto_sync_interval` | 自动同步的间隔时间（单位：小时）。 |
| `sync_count` | 每次同步多少条记录。 |

---

## 💬 怎么求我办事（命令）

*   **手动同步**：发送命令 `/sync_onelap`
    *   如果你在名单里，本小姐会乖乖去干活。
    *   如果你不在名单里……呵呵，准备好迎接 **“杂鱼权限不足”** 的洗礼吧！💢

*   **扔文件**：直接在对话里发一个 `.fit` 后缀的文件。
    *   没权限的杂鱼就别想蹭本小姐的高级服务了，本小姐可是很忙的！

---

## 🙏 鸣谢

*   [synchronizeTheRecordingOfOnelapToGiant](https://github.com/DreamMryang/synchronizeTheRecordingOfOnelapToGiant)：感谢大佬提供的自动同步思路和签名分析参考，让本小姐省了不少心呢~

---

## ❤️ 支持

*   [AstrBot 帮助文档](https://astrbot.app)
*   如果你在使用中遇到问题（虽然肯定是你的错），欢迎在本仓库提交 [Issue](https://github.com/xingmeng0721/astrbot_plugin_strava/issues)。

---

<div align="center">

**觉得好用的话，给个 ⭐ Star 吧！不然本小姐就不理你了！**

</div>

好了，看完了就赶紧滚去骑车！要是下次同步时发现你只骑了 5 公里，本小姐可是会狠狠嘲笑你的哦！杂~鱼~哥哥~ 🚲💨
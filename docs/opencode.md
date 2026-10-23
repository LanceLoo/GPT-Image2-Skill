# OpenCode 自定义服务生图

本仓库根目录的 `SKILL.md` 是唯一的 Skill 入口，面向 OpenCode 使用，也可通过 OpenChamber 发起请求。当前在仓库内开发，不安装或移动到全局目录。开发完成后，可以将整个仓库放入 `~/.agents/skills/` 下的一个子目录，保留根目录 `SKILL.md`、`skills/` 和 `src/` 的相对结构。

启动脚本只加载本仓库源码；源码缺失时直接报错，不调用已安装的其他版本、PATH 中的命令或上游远程包。`tests/` 等开发文件可以继续保留。

## 配置来源

CLI 的 `--opencode-provider "<provider-id>"` 从全局 `~/.config/opencode/opencode.json` 或 `opencode.jsonc` 读取配置；设置 `XDG_CONFIG_HOME` 时使用该目录下的 `opencode/`。两个文件同时存在或都不存在时，必须用 `--opencode-config` 指定。`<provider-id>` 是用户配置中的实际服务标识，不是固定名称或界面显示名称。

支持 `provider[provider-id].options.baseURL/apiKey`，以及 `providers[provider-id].settings.baseURL/apiKey` 两种配置结构。支持 `{env:变量名}`，不支持 `{file:...}`。只读取一个文件，不模拟 OpenCode 多层配置合并，不读取认证存储。指定 OpenCode provider 时不读取 `.env`，不回退到其他 Key 或官方地址。

URL 保留已有 `/v1` 前缀，SDK 追加 `/images/generations`。所选服务必须兼容 OpenAI Images API，并支持所请求的图片模型；能够调用聊天模型并不代表支持生图。已在一个配置的服务上完成手动和 Agent 直接生图验证，其他服务需自行确认兼容性。

## 首次验证（PowerShell）

在仓库根目录运行；`uv` 首次运行会安装脚本依赖：

```powershell
uv run .\skills\gpt-image\scripts\generate.py --opencode-provider "<provider-id>" --model gpt-image-2 -p "一只橘猫坐在窗台上，温暖日光，简洁插画，无文字" --size 1024x1024 --quality medium -n 1 -f .\outputs\first-image.png
```

如需指定配置，在命令中追加 `--opencode-config "配置文件的绝对路径"`。运行前确认输出文件不存在。成功后会打印图片路径，可在本机打开验证。

如果代理的安全规则禁止访问配置或凭据，应由用户在自己的终端执行此命令；不要让代理包装或改写命令规避限制。无需在聊天中提供真实 Key。

API 失败不会自动重试；指定 OpenCode provider 时只报告错误类型和 HTTP 状态，避免网关响应回显凭据。404 通常需要确认路由，401/403 需要确认认证或权限，400 需要确认服务支持的参数。不要仅根据状态码判定根因。

## 离线验证

```powershell
uv run --with-editable . python -m unittest discover -s tests -v
git diff --check
```

离线测试使用临时配置和假 Key，不连接真实服务。

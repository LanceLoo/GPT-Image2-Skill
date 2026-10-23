---
name: gpt-image
description: 使用 OpenCode 中配置的兼容图片接口的服务，根据自然语言描述生成图片并保存本地。通过本仓库 Python 脚本执行。
---

# OpenCode 单张生图

本 Skill 的仓库根目录就是本文件所在目录。先解析绝对路径，调用该目录下的 `skills/gpt-image/scripts/generate.py`。启动脚本只加载本仓库的 `src/gpt_image_cli`，不使用环境中其他安装版本或上游远程包。整个仓库应作为一个完整 Skill 保留，不要单独复制启动脚本。

1. 保留用户的主体、风格、图片内文字和用途；信息足够时直接执行，无需选择图库或再次选择模型。
2. 使用用户指定或当前对话已确认的 provider ID；未确认时先询问，不假定固定名称，也不根据聊天模型推断图片接口可用。默认图片模型为 `gpt-image-2`，需所选服务支持；默认单张、1024x1024、medium 质量。用户指定模型、尺寸或质量时按其要求设置。
3. 使用 `uv run "<仓库绝对路径>/skills/gpt-image/scripts/generate.py" --opencode-provider "<provider-id>" --model gpt-image-2 -p "用户描述" --size 1024x1024 --quality medium -n 1 -f "<输出绝对路径>.png"`，替换占位符并按用户要求调整参数。在 PowerShell 中正确引用路径和提示词，不使用 Bash 的续行符。
4. 默认从全局 OpenCode JSON/JSONC 配置读取 URL 和 Key；如需指定配置，追加 `--opencode-config "<配置路径>"`。不读取或展示 Key，不把 Key 写入命令行或项目文件。凭据访问被安全规则阻止时，停止并让用户在本机终端执行，不通过脚本绕过。
5. 默认输出到当前项目的 `outputs/`，使用时间戳文件名。执行前检查目标不存在，避免覆盖已有图片。
6. 成功后确认图片文件存在且可读取，报告绝对路径、模型、尺寸和质量。失败后报告退出码和脱敏错误，不自动重试或切换接口。

当前流程只做文字生图。配置读取和手动验证说明见仓库 `docs/opencode.md`。

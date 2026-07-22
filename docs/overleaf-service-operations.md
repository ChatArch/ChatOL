# 服务运维与连接

ChatOL 不是 Overleaf 部署器；它连接一个已经运行的 Overleaf 服务，并把常见项目/编译工作流暴露给 Python 和 `oleaf` CLI。部署、升级、备份和公网入口仍应由 Overleaf Toolkit、Docker Compose、nginx、系统服务和运维脚本负责。

## 部署形态

推荐的自托管 Overleaf 路径仍是官方 Overleaf Toolkit / Docker Compose。裸机源码部署理论上可行，但需要自己维护 Node、Redis、Mongo、编译服务、历史服务、反向代理和升级兼容性，运维成本明显更高。

典型连接形态：

```text
Agent / script
  -> oleaf / chatol.workflows
  -> OVERLEAF_SITE_URL
  -> 自托管 Overleaf Web 服务
  -> Overleaf compile backend
```

`OVERLEAF_SITE_URL` 应指向 Agent 能访问的 Overleaf Web 入口：可以是服务端 loopback、内网地址，也可以是经过 TLS/nginx 的公开入口。不要把真实生产域名写进公开文档或公开日志。

## ChatOL 配置边界

ChatOL 的配置代表 Overleaf 服务本身，因此统一使用 `OVERLEAF_*` 字段：

```text
OVERLEAF_SITE_URL              # Overleaf Web 入口
OVERLEAF_ADMIN_EMAIL           # 登录邮箱，敏感
OVERLEAF_ADMIN_PASSWORD        # 登录密码，敏感
OVERLEAF_SESSION_COOKIE        # 现有会话 cookie，敏感
OVERLEAF_SESSION_COOKIE_NAME   # cookie 名，默认 overleaf_session2
OVERLEAF_HTTP_TIMEOUT          # HTTP timeout 秒数
```

不维护 `CHATOL_*` 兼容入口，也不再使用 `OVERLEAF_BASE_URL` / `OVERLEAF_EMAIL` / `OVERLEAF_PASSWORD` 等旧别名。

## 凭据和 session

- 密码和 session cookie 不应作为普通命令参数出现。
- 推荐使用 ChatEnv private profile、进程环境变量、`--password-stdin` 或 `--session-stdin`。
- `chatenv cat -t overleaf` 应只显示 masked 敏感字段。
- 公开输出里要脱敏真实 URL、邮箱、cookie、token、项目 ID 和 build URL。

ChatOL 不维护独立账号体系，也不提供额外 API key。`oleaf` 的权限来自它使用的 Overleaf session：这个 session 能看见和修改哪些项目，`oleaf` 就能通过 Overleaf Web 路由操作哪些项目。

## ChatEnv 默认配置

安装 ChatOL 后，ChatEnv 会注册 `overleaf` 配置类型。可以把 Overleaf 连接信息保存到 active profile，然后直接运行 `oleaf`：

```bash
python -m chatenv.cli init -t overleaf -I
python -m chatenv.cli set OVERLEAF_SITE_URL=https://overleaf.example.com -I
python -m chatenv.cli set OVERLEAF_ADMIN_EMAIL=<email> -I
printf 'OVERLEAF_ADMIN_PASSWORD=%s\n' "$OVERLEAF_PASSWORD" | python -m chatenv.cli paste --stdin -y -I
oleaf doctor --json
```

使用 session cookie 时：

```bash
python -m chatenv.cli set OVERLEAF_SITE_URL=https://overleaf.example.com -I
printf 'OVERLEAF_SESSION_COOKIE=%s\n' "$OVERLEAF_SESSION_COOKIE" | python -m chatenv.cli paste --stdin -y -I
python -m chatenv.cli set OVERLEAF_SESSION_COOKIE_NAME=overleaf_session2 -I
oleaf doctor --json
```

配置优先级是：显式 CLI/Python 参数 > 进程环境变量 > active ChatEnv `overleaf` profile。源码开发环境如果 `python -m chatenv.cli status` 看不到 `Overleaf` provider，先安装包或执行 `pip install -e .` 注册 entry point。

## 内网和公网入口

服务端自动化优先使用 Overleaf 同机 loopback 或内网入口，减少公网暴露面：

```bash
export OVERLEAF_SITE_URL="http://127.0.0.1:<port>"
oleaf doctor --json
```

如果需要公网入口，建议由 nginx/TLS 负责认证边界、host header、上传体积、超时和日志策略。ChatOL 只负责按 HTTP session 访问 Overleaf 页面和内部 JSON route。

## 安全约束

- CLI JSON 默认不输出内部编译 URL、项目所有者/更新者元数据。
- 编译产物下载会拒绝跨源 URL，避免把认证头或 cookie 发给非 Overleaf 主机。
- 删除、同步上传、管理员操作必须默认 dry-run 或要求显式 `--apply`。

## 运维检查清单

| 检查项 | 建议 |
| --- | --- |
| Overleaf 服务状态 | 先用浏览器或服务端健康检查确认 Web 可登录 |
| Agent 网络路径 | 确认运行 `oleaf` 的机器能访问 `OVERLEAF_SITE_URL` |
| 凭据来源 | 使用 private env/profile/stdin，不写入仓库 |
| 编译能力 | 用小项目跑 `oleaf compile run` 和 `oleaf compile output ... log` |
| 输出脱敏 | 公开输出不要包含真实 URL、cookie、token、项目 ID 或 build URL |

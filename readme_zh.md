# Harness Passkey Gateway

**用通行密钥，从自己的手机与电脑访问 Agent 工作区。**

[English](README.md) · [架构](docs/architecture.md) · [安全说明](SECURITY.md)

为 DeepSeek Harness 提供可自行部署的访问网关：通过 Pocket ID 等 OIDC 身份服务使用 Passkey 登录，在服务器端衔接 Harness 原有认证。

> 当前处于开发阶段，程序与部署说明将分批提交。本项目与 DeepSeek、Pocket ID、Cloudflare、frp 均无隶属关系。

## 设计目标

- 手机、Windows、macOS 分别登记密钥，同一个账户管理多台设备。
- 服务端保存会话，默认绝对有效期上限 90 天，闲置 7 天到期，并支持撤销。
- Harness 的启动令牌和上游会话 Cookie 留在服务器，不交给浏览器。
- 支持流式响应与经过认证的 WebSocket。
- HTTPS 反向代理，可配合 frp TCP 隧道发布入口。
- 仓库仅包含通用配置示例，不包含生产域名、密钥或设备资料。

## 使用前提

需要浏览器支持 WebAuthn、可信 HTTPS 域名，以及兼容的 OIDC 身份服务。鸿蒙手机应验证实际浏览器；系统提供 FIDO2 能力并不等于所有浏览器都可用。指纹、面容或设备 PIN 验证需要本人完成。

## 脱敏约定

生产配置保存在仓库外。请勿提交 API Key、证书私钥、OIDC 客户端密钥、Harness 启动令牌、会话数据库、设备清单和带凭据的截图。详见 [SECURITY.md](SECURITY.md)。

## 许可

[MIT](LICENSE)。上游项目的许可与商标保持独立。

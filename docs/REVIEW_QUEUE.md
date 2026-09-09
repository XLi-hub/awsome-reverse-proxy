# 首轮人工审核队列

本文是对 `data/inbox/*.yaml` 中当前 74 个候选的风险分流。首轮已有 52 项进入正式目录，22 项保留为 `needs-review`，另有 2 项完成排除处理；静态研究快照日期为 2026-09-08，元数据与审核状态更新于 2026-09-09。

“已确认”表示风险触发条件可以由项目自己的 GitHub 仓库、README、许可证或维护者公告直接证明；“待确认”表示仍缺少足以决定 `accepted`、`historical` 或 `rejected` 的证据。正式审核结论以 `data/reviews/*.yaml` 和 `data/projects.yaml` 为准。

## 1. 裁决原则

- 归档或官方明确弃用：活跃目录不收录；有历史价值时转入 `historical`。
- 维护模式：保持 `needs-review`，除非能证明仍有安全修复、兼容性维护和可用发布；否则只进入历史附录。
- 实验性或可能破坏兼容：不得写成稳定推荐；只能进入“实验/潜力项目”，并把成熟度限制写入展示文案。
- 迁移或拆仓：先确定当前规范上游和继任关系，再计算 Star、Release 与活跃度；旧仓库与新仓库不得重复计数。
- 托管控制面依赖：可以收录，但必须明确区分“仓库内可自托管部分”和“依赖厂商服务的完整体验”。
- 边界较弱：必须证明反向代理、入口网关或反向隧道是可独立使用的正式能力，而非仅在架构中间接出现。
- 复杂或非标准许可证：在许可证字段能够准确表达版本、目录和发行物差异前暂停收录；不得仅照抄 GitHub 自动识别的 SPDX 标签。

## 2. 已处理 / 已排除

| 项目 | 已确认事实 | 处理结果 |
|---|---|---|
| [`minio/sidekick`](https://github.com/minio/sidekick) | GitHub 显示仓库已由所有者于 2026-07-14 归档并只读。 | 已从活跃候选移除并写入 `data/rejected.yaml`；如保留历史价值，应只在 `historical` 附录展示。 |
| [`varnishcache/varnish-cache`](https://github.com/varnishcache/varnish-cache) | GitHub 显示仓库已归档；README 明确说明开发已迁移到 [`code.vinyl-cache.org`](https://code.vinyl-cache.org/)。 | 已从活跃候选移除并写入 `data/rejected.yaml`；后续如评估新上游，应作为新的候选身份独立审核，不继承旧仓库的实时状态。 |

以上两项不再进入下列待裁决批次。

### GitHub License 自动识别阻断

元数据抓取对以下项目返回 `NOASSERTION`。它们并非被判定为无许可证，而是单一 SPDX 字段不足以支撑正式收录，因此保持 `needs-review`：

- [`flomesh-io/pipy`](https://github.com/flomesh-io/pipy)
- [`haproxy/haproxy`](https://github.com/haproxy/haproxy)
- [`http-party/node-http-proxy`](https://github.com/http-party/node-http-proxy)
- [`openresty/openresty`](https://github.com/openresty/openresty)
- [`yusing/godoxy`](https://github.com/yusing/godoxy)
- [`zalando/skipper`](https://github.com/zalando/skipper)

后续需核对根目录、子目录和发行物许可证；不能仅依据项目知名度手工猜测 SPDX 值。

## 3. P0：先裁决的阻断项

| 项目 | 状态 | 具体风险与当前证据 | 建议动作 | 每项最低补证 |
|---|---|---|---|---|
| [`mholt/caddy-l4`](https://github.com/mholt/caddy-l4#project-conncept-a-tcpudp-app-for-caddy) | 已确认 | README 明示项目是 experimental、仍在开发且应预期破坏性变更；同时说明它不是 Caddy 组织的官方仓库。 | 保持 `needs-review`；若收录，仅进入实验/潜力分组，不能作为稳定 Caddy L4 官方实现介绍。 | README 成熟度声明；最近正式 Release 或 tag；与当前 Caddy 版本的兼容矩阵；维护者对稳定 API 的承诺。 |
| [`yyyar/gobetween`](https://github.com/yyyar/gobetween#readme) | 已确认 | README 明示“Maintenance mode, accepting PRs”。维护模式不等于废弃，但不足以支撑活跃推荐。 | 保持 `needs-review`；根据发布和安全维护证据决定活跃收录或 `historical`。 | 维护声明；最后两个 Release 的日期与内容；近 12 个月合并的非机器人修复；安全问题响应方式。 |
| [`azukaar/Cosmos-Server`](https://github.com/azukaar/Cosmos-Server#licence) | 已确认 | README 声明采用 Apache-2.0 加 Commons Clause，并明确禁止出售软件、衍生品或基于它提供服务；不能把它简写为 Apache-2.0，也不应无说明地称为标准开源许可证。 | 暂停正式收录；若目录坚持只收录开源软件则 `rejected`，否则仅放入明确标注的 source-available 附录。 | 仓库 LICENSE 全文；README 的 Commons Clause 说明；项目对 SaaS/再分发/商业使用的官方解释；目录是否允许 source-available 的政策裁决。 |
| [`gravitational/teleport`](https://github.com/gravitational/teleport#license) | 已确认 | 仓库 README 说明 `/api` 为 Apache-2.0、其余源代码为 AGPL；官方 Community Edition 二进制使用带组织规模和营收限制的修改版 Apache 许可证，见 [`LICENSE-community`](https://github.com/gravitational/teleport/blob/master/build.assets/LICENSE-community)。“源码许可证”和“官方构建许可证”不能混写。 | 许可证完成逐层建模前暂停；即使收录，也必须注明源代码自行构建与官方 Community Edition 构建的许可差异。 | 根目录和 `/api` 许可证；目标版本的 `LICENSE-community`；所推荐安装方式对应的发行物许可证；反向代理能力所在模块是否落在同一授权范围。 |
| [`cloudflare/cloudflared`](https://github.com/cloudflare/cloudflared#cloudflare-tunnel-client) | 已确认 | README 将该仓库定义为 Cloudflare Tunnel 的客户端/连接器，流量入口由 Cloudflare 网络承担，并要求通过 Cloudflare 账户/控制面创建和路由隧道；它不是完整可自托管的隧道服务。 | 可以保留，但必须标为“开源客户端 + 托管边缘/控制面”，并与完整自托管隧道分组或加醒目标记。 | README 的组件边界；生产建隧道所需账户与控制面；服务端/边缘是否可自托管；免费层与协议限制的官方文档。 |

## 4. P1：迁移、拆仓与上游身份

| 项目 | 状态 | 具体风险与当前证据 | 建议动作 | 每项最低补证 |
|---|---|---|---|---|
| [`Kong/kubernetes-ingress-controller`](https://github.com/Kong/kubernetes-ingress-controller#kic-and-kong-operator) | 已确认 | README 说明 KIC 会继续按支持政策维护，但 Kubernetes 上的所有新功能转向 [`Kong/kong-operator`](https://github.com/Kong/kong-operator)。它仍受支持，却已不是新功能的主入口。 | 不直接判历史项目；核对支持截止时间后决定保留为维护中项目，或以 Kong Operator 为主、KIC 为兼容条目。 | KIC 支持周期页面；最近稳定 Release；Operator 是否完整覆盖 KIC；官方迁移指南。 |
| [`kgateway-dev/kgateway`](https://github.com/kgateway-dev/kgateway#history) | 已确认 | README 说明它由 Gloo 迁移/更名而来；同时说明从 2.3.0 起 agentgateway 的控制面已迁往 [`agentgateway/agentgateway`](https://github.com/agentgateway/agentgateway)。历史 Star 与当前产品边界需要按迁移关系解释。 | 当前 URL 可作为规范上游，但描述只写 Envoy API Gateway 能力；AI/agent 能力需按新拆仓重新核验，禁止重复计数。 | 官方迁移计划；仓库转移/更名链；2.3.0 后数据面说明；当前 Release 与文档域名。 |
| [`rathole-org/rathole`](https://github.com/rathole-org/rathole/discussions/416) | 已确认 | 维护者公告说明仓库已从个人账户转移到 `rathole-org`，原作者因精力原因交接给新维护者。候选 URL 是当前地址，但需记录转移事实以防抓取缓存仍指向旧 slug。 | 保留当前 URL；审核维护交接后的发布连续性，不把旧、新 URL 当成两个项目。 | 置顶转移公告；GitHub 重定向结果；交接后至少一个正式 Release；当前维护者名单。 |
| [`localtunnel/localtunnel`](https://github.com/localtunnel/localtunnel#readme) | 已确认 | 候选仓库只包含客户端；完整自托管服务端在 [`localtunnel/server`](https://github.com/localtunnel/server#localtunnel-server)。把客户端仓库单独描述为“自托管隧道服务”会遗漏核心服务端。 | 将两仓库作为一个项目族展示，或把候选主仓库改为服务端并关联客户端；不得暗示单仓即完整自托管实现。 | 客户端 `--host` 文档；服务端 README/部署方式；两仓许可证；两端最近 Release/提交和兼容关系。 |
| [`apache/apisix-ingress-controller`](https://github.com/apache/apisix-ingress-controller/blob/master/docs/en/latest/upgrade-guide.md) | 已确认 | 官方 1.x→2.0 升级指南列出架构变化、移除 mock-etcd、多项字段和 CRD 移除，并要求特定 APISIX 数据面版本。候选的概括本身没有错，但若不绑定版本会隐藏重大兼容差异。 | 可继续审核；正式条目必须以当前 2.x 架构描述，并把 1.x 迁移限制写入 `limitations`。 | 最新稳定 Release；升级指南；支持的 Kubernetes/APISIX/Gateway API 版本矩阵；废弃 CRD 列表。 |

## 5. P1：许可证和版本/目录边界

| 项目 | 状态 | 具体风险与当前证据 | 建议动作 | 每项最低补证 |
|---|---|---|---|---|
| [`TykTechnologies/tyk`](https://github.com/TykTechnologies/tyk#license) | 已确认 | README 声明除 `ee` 目录外为 MPL-2.0，`ee` 为商业许可证；管理控制面、Dashboard 和开发者门户被作为 Enterprise API Management 产品介绍。 | 网关核心可继续审核，但 License 不能覆盖成单一值；展示中区分开源 Gateway 与商业管理面。 | 根 LICENSE；`ee` 许可证；无 Dashboard 时可独立运行的官方步骤；功能是否落入 `ee` 的清单。 |
| [`fosrl/pangolin`](https://github.com/fosrl/pangolin#deployment-options) | 已确认 / 待裁决 | README 同时列出 AGPL-3 Community、商业许可 Enterprise 和托管 Cloud；项目可自托管，但不同版本的功能与许可边界不同。README 也确认反代能力存在，但新定位已扩展为 SASE、VPN、PAM 和 AI 网关，仍需确认 Community Edition 实际包含候选描述中的反代、SSO、TCP/UDP 能力。 | 可保留；License 和部署方式按 Community/Enterprise/Cloud 分开记录，逐项核对 CE 功能后再定描述和标签。 | 仓库 LICENSE；Community 自托管与功能清单；反代/SSO/TCP/UDP 的 CE 配置示例；Enterprise 专属功能；发布镜像对应的 edition。 |
| [`netbirdio/netbird`](https://github.com/netbirdio/netbird#legal) | 已确认 | README 的 Legal 段落说明仓库大部分为 BSD-3-Clause，而 `management/`、`signal/`、`relay/` 为 AGPL-3.0；完整自托管恰好涉及这些服务。 | 可保留，但 License 应表达目录级混合授权；抓取器的单一 GitHub license 值不足以完成审核。 | 根 LICENSE；三个子目录 LICENSE；官方自托管组成图；所推荐镜像的源代码与许可证对应关系。 |

## 6. P1：与反向代理目录边界较弱

这些项目并非质量较差；风险在于它们的主要产品边界比“反向代理”宽得多。若保留，应在独立的服务网格/零信任分组中展示，不能和通用反代按同一维度直接排名。

| 项目 | 状态 | 具体边界问题 | 建议动作 | 每项最低补证 |
|---|---|---|---|---|
| [`cilium/cilium`](https://github.com/cilium/cilium) | 待确认 | 主体是 eBPF Kubernetes 网络、安全与可观测平台，Ingress/Gateway API/服务网格只是能力集合的一部分。 | 仅在能证明无需另一个候选控制面即可提供正式入口网关时保留。 | 官方 Gateway API/Ingress 文档；数据路径中 Envoy 的角色；最小可部署示例；功能成熟度/支持级别。 |
| [`istio/istio`](https://github.com/istio/istio) | 待确认 | 主体是服务网格控制平面，入口/出口网关是网格部署角色，而不是通用独立反代产品。 | 保留在 `service-mesh-gateway` 的前提是条目聚焦网格边界流量，不把整个 Istio 评分为反代。 | 官方 ingress/egress gateway 文档；Gateway API 支持状态；独立部署要求；对应数据平面。 |
| [`kumahq/kuma`](https://github.com/kumahq/kuma) | 待确认 | 主体是多区域服务网格；内置网关与 delegated gateway 的责任不同，候选描述容易把两者合并。 | 明确内置网关是否实际代理应用流量；若使用 delegated gateway，应列出外部数据面依赖。 | 官方 builtin/delegated gateway 对比；数据平面组件；入口流量配置示例；支持状态。 |
| [`openziti/ziti`](https://github.com/openziti/ziti) | 待确认 | 该仓库主要是 OpenZiti 控制器和路由器；候选所述“通过隧道器接入既有服务”还依赖其他 tunneler/客户端仓库，且更接近零信任覆盖网络。 | 考虑移出反代主目录；若保留，以项目族形式列全必需组件，并证明存在反向入口语义。 | 官方架构图；必需仓库清单；服务端/客户端流量路径；反向代理或无入站端口的正式用例。 |
| [`netbirdio/netbird`](https://github.com/netbirdio/netbird) | 待确认 | 核心是 WireGuard 覆盖网络和访问策略，不是 HTTP/TCP 反向代理；中继也不自动等同于反向隧道产品。 | 优先归入相邻技术或扩展阅读；只有正式的服务发布/反向入口能力得到证明时才留在主目录。 | 官方流量路径；入站服务发布能力；是否需要客户端组网；与反向隧道的差异。 |
| [`tailscale/tailscale`](https://github.com/tailscale/tailscale/blob/main/README.md) | 已确认 / 待裁决 | README 将仓库定位为包含 `tailscaled` 和 CLI 的开源代码，并称只包含 Tailscale 的“大部分”开源代码；控制服务器不在该仓库内。候选依赖 Serve/Funnel 子功能，核心仍是 WireGuard 组网。 | 若保留，标为“托管控制面下的服务发布子功能”，并与通用反代、完整自托管隧道分开；可关联 [`juanfont/headscale`](https://github.com/juanfont/headscale) 说明自托管控制面的第三方实现。 | 官方 Serve/Funnel 文档；控制面是否开源/可自托管；公网入口数据路径；免费与付费限制。 |
| [`gravitational/teleport`](https://github.com/gravitational/teleport#introduction) | 已确认 / 待裁决 | README 定位为覆盖 SSH、Kubernetes、数据库、桌面、Web 等资源的身份访问平台；反向隧道和应用代理是其中一部分，而非通用反代。 | 与许可证阻断项合并审核；只有“Application Access/反向隧道”可独立、且目录接受零信任平台时保留。 | Application Access 架构；反向隧道组件；最小自托管部署；Community 版本是否包含所述能力。 |
| [`azukaar/Cosmos-Server`](https://github.com/azukaar/Cosmos-Server#readme) | 已确认 / 待裁决 | README 将它同时定位为家庭服务器管理器、安全网关、应用商店、容器管理和反代；反代虽重要，但不是唯一产品边界。 | 许可证问题若允许进入附录，再决定放在管理面板还是家庭服务器平台，不进入通用反代排序。 | 实际代理运行时；反代是否可独立于容器管理使用；最小权限部署；与管理平台功能边界。 |

## 7. P2：商业控制面或发行版边界需显式标注

以下项目不因存在商业产品而自动降级；审核目标是避免把“开源核心”“官方发行物”和“托管产品”混成一个对象。

| 项目 | 状态 | 触发原因 | 每项最低补证 |
|---|---|---|---|
| [`cloudflare/cloudflared`](https://github.com/cloudflare/cloudflared) | 已确认 | 仓库是连接 Cloudflare 网络的 connector，公网入口和控制面不在仓库内。 | 自托管边界；账户/域名要求；控制面和边缘的运营方；官方支持窗口。 |
| [`tailscale/tailscale`](https://github.com/tailscale/tailscale) | 已确认 | 仓库包含主要客户端/守护进程代码，但不等于完整 Tailscale 服务端。 | 控制服务器源码边界；默认服务依赖；Headscale 兼容性是否由 Tailscale 官方支持；Serve/Funnel 限制。 |
| [`TykTechnologies/tyk`](https://github.com/TykTechnologies/tyk) | 已确认 | 开源 Gateway 与商业 `ee`、Dashboard/管理控制面同仓或同产品线出现。 | 纯开源部署闭环；管理 API；商业专属功能；各目录许可证。 |
| [`exposedev/expose`](https://github.com/exposedev/expose#managed-expose--expose-pro-) | 已确认 | README 同时提供 MIT 自托管服务、托管服务和 Expose Pro；商业服务是可选项，不是已确认依赖。 | 自托管服务端步骤；MIT 发行物；托管/Pro 专属功能；默认客户端是否可指向自建服务端。 |
| [`fosrl/pangolin`](https://github.com/fosrl/pangolin#deployment-options) | 已确认 | Community、Enterprise 与 Cloud 三种部署/许可模式并列。 | CE 完整部署；控制面是否全部自托管；商业功能差异；镜像 edition。 |

## 8. 审核批次建议

### 批次 0：机器预检（当前 74 项）

一次性获取并冻结 `fetched_at`、规范 `full_name`、重定向后的 URL、`fork`、`archived`、License API 值、默认分支、最近 push、最近 Release。任何重定向、归档、无许可证或超过活跃度阈值的项目自动进入人工队列。机器结果只产生风险信号，不直接判定“停止维护”。

### 批次 1：硬阻断（优先完成）

按顺序审核 Cosmos Server、Teleport、caddy-l4、gobetween、cloudflared。该批次会直接决定哪些项目不能进入首版活跃目录，也会验证数据模型能否表达实验性、source-available 和托管依赖。Sidekick 与 Varnish Cache 已完成排除，不再重复审核。

### 批次 2：迁移与拆仓

审核 Kong KIC、kgateway、rathole、localtunnel、APISIX Ingress Controller。先冻结“项目族 ID”和规范上游，再抓 Star/Release，避免指标错配或重复收录。

### 批次 3：目录边界

审核 Cilium、Istio、Kuma、OpenZiti、NetBird、Tailscale、Teleport、Cosmos Server。建议由两名审核者独立回答同一问题：“删除周边平台能力后，候选仍是否提供可独立说明的反代、入口或反向隧道能力？”不一致时保持 `needs-review`。

### 批次 4：许可证与商业边界

审核 Tyk、Pangolin、NetBird，并复核前述 Teleport、Cosmos Server、cloudflared。先记录源码、目录、二进制/镜像、Community/Enterprise/Cloud 四层许可与依赖，再写用户可见描述。

### 批次 5：常规候选

其余项目按分类分批审核，每批 10–15 个。先核规范上游和核心用途，再核 License、发布、文档和工程质量；不要先按 Star 排序，以免审核者产生头部偏见。

## 9. 单项审核的最小证据包

每个候选进入 `accepted` 前，审核记录至少附以下可复查证据：

1. **身份**：GitHub 规范 URL、是否重定向、组织/维护者对上游身份的说明。
2. **范围**：README 或官方文档中直接描述反向代理、入口流量或反向隧道为正式能力的段落。
3. **状态**：`archived`、维护/弃用声明、最后稳定 Release、最近一次非机器人实质提交；四者必须分开记录。
4. **许可证**：根目录 LICENSE；若为 monorepo、双许可或分 edition，再附子目录和发行物许可证，写出适用对象。
5. **可运行性**：最小部署文档、必需外部组件、是否依赖厂商账户/控制面/边缘网络。
6. **成熟度**：稳定性声明、版本兼容矩阵、升级/迁移文档；实验能力必须原样标注风险。
7. **描述核对**：逐项证明中文描述、协议、部署标签和 `limitations`，并记录 `reviewed_at`。

证据优先级为：仓库状态/API与 LICENSE > 维护者公告/README > 官方版本文档与 Release > Issue/Discussion。搜索结果、第三方 Awesome 列表、博客和 Star 数只能帮助定位证据，不能单独支持收录结论。

<!-- 此文件由 scripts/generate_readme.py 生成，请勿手工编辑。 -->

# 正式项目目录

本页仅展示状态为 `accepted` 的项目。Star 是抓取快照；信号分用于目录排序，不代表绝对质量。

## 通用反向代理

| 项目 | 客观简介 | 标签 | License | Star | 最新 Release | 信号分 | 最后复核日 |
|---|---|---|---|---:|---|---:|---|
| [Caddy](https://github.com/caddyserver/caddy) | 默认自动管理 HTTPS 的模块化 Web 服务器与反向代理。 | http、https、automatic-https、load-balancing、go、modular | Apache-2.0 | 78,141 | v2.11.7 | 99.0 | 2026-09-09 |
| [Traefik Proxy](https://github.com/traefik/traefik) | 支持动态服务发现的云原生应用代理与边缘路由器。 | http、tcp、udp、docker、kubernetes、service-discovery、automatic-https | MIT | 65,276 | v3.7.15 | 98.8 | 2026-09-09 |
| [NGINX](https://github.com/nginx/nginx) | 高性能 Web 服务器、反向代理、负载均衡器与内容缓存。 | http、https、tcp、udp、load-balancing、caching、tls | BSD-2-Clause | 31,914 | release-1.31.7 | 97.7 | 2026-09-09 |
| [H2O](https://github.com/h2o/h2o) | 针对 HTTP/1、HTTP/2 与 HTTP/3 优化的 Web 服务器和反向代理。 | http1、http2、http3、quic、reverse-proxy、tls | MIT | 11,549 | tag-no-more-releases | 86.3 | 2026-09-09 |
| [Apache HTTP Server](https://github.com/apache/httpd) | 模块化 HTTP 服务器，可通过 mod\_proxy 提供反向代理与负载均衡。 | http、https、reverse-proxy、load-balancing、modules、tls | Apache-2.0 | 4,041 | — | 82.1 | 2026-09-09 |
| [Tengine](https://github.com/alibaba/tengine) | 源自淘宝、兼容 NGINX 的高性能 Web 服务器与反向代理。 | nginx、http、http3、reverse-proxy、load-balancing、health-check | BSD-2-Clause | 13,397 | 3.1.0 | 77.0 | 2026-09-09 |

## 负载均衡器

| 项目 | 客观简介 | 标签 | License | Star | 最新 Release | 信号分 | 最后复核日 |
|---|---|---|---|---:|---|---:|---|
| [fabio](https://github.com/fabiolb/fabio) | 通过 Consul 服务发现自动配置的 HTTP(S) 与 TCP 负载均衡路由器。 | go、consul、service-discovery、http、tcp、load-balancing | MIT | 7,348 | v1.8.0 | 90.4 | 2026-09-09 |
| [LoxiLB](https://github.com/loxilb-io/loxilb) | 面向云原生与边缘场景的 eBPF 云原生负载均衡器。 | ebpf、layer4、kubernetes、nat、load-balancing、observability | Apache-2.0 | 1,885 | v0.9.8.8 | 86.5 | 2026-09-09 |
| [Katran](https://github.com/facebookincubator/katran) | 基于 Linux eBPF/XDP 的高性能 Layer 4 负载均衡器。 | ebpf、xdp、layer4、load-balancing、linux、high-performance | GPL-2.0 | 5,367 | — | 81.9 | 2026-09-09 |
| [Seesaw](https://github.com/google/seesaw) | 基于 Linux Virtual Server 的高可用负载均衡平台。 | lvs、ipvs、layer4、anycast、dsr、high-availability、go | Apache-2.0 | 5,675 | — | 75.9 | 2026-09-09 |

## 轻量或嵌入式代理

| 项目 | 客观简介 | 标签 | License | Star | 最新 Release | 信号分 | 最后复核日 |
|---|---|---|---|---:|---|---:|---|
| [nginx-proxy](https://github.com/nginx-proxy/nginx-proxy) | 根据 Docker 容器元数据自动生成配置的 NGINX 反向代理。 | nginx、docker、service-discovery、automatic-configuration、http、tls | MIT | 19,931 | 1.11.6 | 91.4 | 2026-09-09 |
| [Sōzu](https://github.com/sozu-proxy/sozu) | 使用 Rust 构建、支持运行时热配置的轻量反向代理。 | rust、http、http2、tcp、udp、tls、hot-reload | AGPL-3.0 | 3,745 | 2.3.2 | 90.4 | 2026-09-09 |
| [tcpproxy](https://github.com/inetaf/tcpproxy) | 可按静态规则、HTTP Host 与 TLS SNI 路由连接的 Go TCP 代理。 | go、tcp、sni、tls、host-routing、library、single-binary | Apache-2.0 | 1,301 | — | 72.1 | 2026-09-09 |

## 代理开发库

| 项目 | 客观简介 | 标签 | License | Star | 最新 Release | 信号分 | 最后复核日 |
|---|---|---|---|---:|---|---:|---|
| [Pingora](https://github.com/cloudflare/pingora) | 用于构建高性能、可靠且可编程网络服务的 Rust 代理框架。 | rust、http、http2、grpc、websocket、load-balancing、framework | Apache-2.0 | 27,647 | 0.9.0 | 93.8 | 2026-09-09 |
| [YARP](https://github.com/dotnet/yarp) | 基于 ASP.NET Core 构建可定制高性能 HTTP 反向代理的工具包。 | dotnet、aspnet-core、http、reverse-proxy、load-balancing、library | MIT | 9,628 | v2.3.0 | 82.2 | 2026-09-09 |
| [Oxy](https://github.com/vulcand/oxy) | 用于组合 HTTP 代理、负载均衡与流量控制的 Go 中间件库。 | go、http、reverse-proxy、load-balancing、circuit-breaker、rate-limiting、middleware | Apache-2.0 | 2,104 | — | 79.7 | 2026-09-09 |
| [grpc-proxy](https://github.com/mwitkow/grpc-proxy) | 支持透明转发和自定义路由的 Go gRPC 反向代理库。 | go、grpc、http2、reverse-proxy、routing、library | Apache-2.0 | 1,050 | — | 68.0 | 2026-09-09 |

## 云原生代理数据平面

| 项目 | 客观简介 | 标签 | License | Star | 最新 Release | 信号分 | 最后复核日 |
|---|---|---|---|---:|---|---:|---|
| [Envoy Proxy](https://github.com/envoyproxy/envoy) | 面向云原生服务的高性能四层与七层代理，提供动态 xDS 配置、服务发现、负载均衡和可观测性。 | http、tcp、udp、grpc、xds、load-balancing、service-mesh、kubernetes | Apache-2.0 | 29,089 | v1.40.0 | 97.1 | 2026-09-09 |
| [MOSN](https://github.com/mosn/mosn) | Go 编写的模块化云原生网络代理，可用作四层与七层负载均衡器、服务网格数据平面或入口网关。 | http、tcp、udp、tls、service-mesh、ingress、api-gateway、wasm | Apache-2.0 | 4,508 | v1.6.1 | 70.9 | 2026-09-09 |

## Kubernetes Ingress Controller

| 项目 | 客观简介 | 标签 | License | Star | 最新 Release | 信号分 | 最后复核日 |
|---|---|---|---|---:|---|---:|---|
| [NGINX Ingress Controller](https://github.com/nginx/kubernetes-ingress) | NGINX 官方维护的 Kubernetes Ingress Controller，支持 NGINX 开源版和 NGINX Plus 数据平面。 | http、https、tls、nginx、ingress、gateway-api、kubernetes | Apache-2.0 | 5,085 | v5.7.0 | 92.9 | 2026-09-09 |
| [Envoy Gateway](https://github.com/envoyproxy/gateway) | 管理 Envoy Proxy 的应用网关，支持以 Kubernetes Gateway API 配置入口流量和策略。 | http、grpc、envoy、gateway-api、kubernetes、xds | Apache-2.0 | 3,086 | v1.9.2 | 91.3 | 2026-09-09 |
| [Contour](https://github.com/projectcontour/contour) | 使用 Envoy 作为数据平面的 Kubernetes 入口控制器，支持 Ingress、HTTPProxy CRD 和 Gateway API。 | http、https、envoy、ingress、gateway-api、kubernetes、cncf | Apache-2.0 | 3,958 | v1.33.7 | 89.3 | 2026-09-09 |
| [HAProxy Ingress](https://github.com/jcmoraisjr/haproxy-ingress) | 社区维护的 HAProxy Kubernetes Ingress Controller，提供注解、ConfigMap 和自定义资源驱动的路由配置。 | http、https、tcp、tls、haproxy、ingress、kubernetes | Apache-2.0 | 1,172 | v0.16.2 | 88.5 | 2026-09-09 |
| [HAProxy Kubernetes Ingress Controller](https://github.com/haproxytech/kubernetes-ingress) | HAProxy Technologies 维护的 Kubernetes 入口控制器，以 HAProxy 处理集群外部到服务的流量。 | http、https、tcp、tls、haproxy、ingress、kubernetes | Apache-2.0 | 870 | v3.2.17 | 87.7 | 2026-09-09 |
| [APISIX Ingress Controller](https://github.com/apache/apisix-ingress-controller) | 使用 Gateway API 和 APISIX 自定义资源动态管理 Apache APISIX 数据平面的 Kubernetes 控制器。 | http、grpc、ingress、gateway-api、kubernetes、apisix | Apache-2.0 | 1,147 | 2.2.0 | 86.4 | 2026-09-09 |

## API 网关

| 项目 | 客观简介 | 标签 | License | Star | 最新 Release | 信号分 | 最后复核日 |
|---|---|---|---|---:|---|---:|---|
| [Kong Gateway](https://github.com/Kong/kong) | 基于 OpenResty 的 API、AI 与 MCP 网关，提供动态路由、负载均衡、鉴权和插件扩展。 | http、https、grpc、api-management、plugins、kubernetes、ai-gateway | Apache-2.0 | 44,279 | 3.9.4 | 97.9 | 2026-09-09 |
| [Apache APISIX](https://github.com/apache/apisix) | 基于 OpenResty 和 etcd 的动态 API 网关，覆盖七层路由、四层代理、流量治理和插件扩展。 | http、https、tcp、udp、grpc、api-management、plugins、kubernetes | Apache-2.0 | 17,239 | 3.19.0 | 95.6 | 2026-09-09 |
| [Higress](https://github.com/higress-group/higress) | 基于 Envoy 和 Istio 技术栈的云原生 API 与 AI 网关，支持 Kubernetes 服务发现和 Wasm 插件。 | http、grpc、envoy、istio、wasm、kubernetes、ai-gateway | Apache-2.0 | 9,587 | v2.2.5 | 93.8 | 2026-09-09 |
| [Ocelot](https://github.com/ThreeMammals/Ocelot) | 面向 .NET 的 API 网关库，通过应用内配置提供路由、聚合、鉴权、限流和服务发现。 | http、dotnet、api-aggregation、rate-limiting、service-discovery、library | MIT | 8,717 | 25.0.2 | 93.8 | 2026-09-09 |
| [Spring Cloud Gateway](https://github.com/spring-cloud/spring-cloud-gateway) | 基于 Spring 的 API 网关，为 JVM 微服务提供路由、过滤器、限流和服务发现集成。 | http、spring、java、filters、rate-limiting、service-discovery | Apache-2.0 | 4,914 | v5.0.3 | 91.1 | 2026-09-09 |
| [KrakenD Community Edition](https://github.com/krakend/krakend-ce) | Go 编写的无状态声明式 API 网关，侧重请求聚合、转换、路由和中间件组合。 | http、api-aggregation、stateless、declarative-config、middleware、golang | Apache-2.0 | 2,691 | v3.0.1 | 90.5 | 2026-09-09 |
| [Envoy AI Gateway](https://github.com/envoyproxy/ai-gateway) | 构建在 Envoy Gateway 之上的生成式 AI 流量网关，提供统一后端、凭据策略、路由和令牌级治理。 | http、envoy、gateway-api、kubernetes、ai-gateway、rate-limiting、observability | Apache-2.0 | 2,241 | v1.2.0 | 90.0 | 2026-09-09 |
| [Apache ShenYu](https://github.com/apache/shenyu) | Java 原生 API 网关，提供服务代理、协议转换、动态流量控制和可插拔治理能力。 | http、grpc、dubbo、websocket、mqtt、protocol-conversion、plugins、java | Apache-2.0 | 8,895 | v2.7.1 | 89.9 | 2026-09-09 |
| [Emissary-ingress](https://github.com/emissary-ingress/emissary) | 基于 Envoy 的 Kubernetes 原生七层负载均衡器与 API 网关，使用 CRD 管理入口流量。 | http、grpc、envoy、ingress、kubernetes、crd、rate-limiting | Apache-2.0 | 4,520 | v4.1.0 | 87.3 | 2026-09-09 |
| [WSO2 API Manager](https://github.com/wso2/product-apim) | 集 API 网关、生命周期管理、开发者门户和分析集成于一体的 API 管理平台。 | http、api-management、policies、developer-portal、kubernetes、java | Apache-2.0 | 1,039 | v4.7.0 | 84.7 | 2026-09-09 |
| [Easegress](https://github.com/easegress-io/easegress) | Go 编写的云原生流量编排系统，通过可组合管道提供反向代理、API 治理与韧性策略。 | http、http3、mqtt、traffic-orchestration、service-discovery、wasm、kubernetes | Apache-2.0 | 5,869 | v2.11.0 | 84.5 | 2026-09-09 |
| [Gravitee API Management](https://github.com/gravitee-io/gravitee-api-management) | 包含网关、管理 API 和开发者门户的 API 管理平台，支持同步 API 与事件驱动 API。 | http、api-management、event-driven、policies、developer-portal、kubernetes | Apache-2.0 | 461 | — | 75.9 | 2026-09-09 |

## 服务网格网关

暂无已通过审核的项目。

## 反向隧道与内网穿透

| 项目 | 客观简介 | 标签 | License | Star | 最新 Release | 信号分 | 最后复核日 |
|---|---|---|---|---:|---|---:|---|
| [frp](https://github.com/fatedier/frp) | 面向 NAT 与防火墙后服务暴露的客户端/服务端反向代理与内网穿透工具。 | tcp、udp、http、https、nat-traversal | Apache-2.0 | 109,992 | v0.71.1 | 100.0 | 2026-09-09 |
| [Chisel](https://github.com/jpillora/chisel) | 通过 HTTP 传输并使用 SSH 加密的单文件 TCP/UDP 隧道，支持反向端口转发。 | tcp、udp、http、ssh、reverse-port-forwarding | MIT | 16,663 | v1.12.0 | 92.7 | 2026-09-09 |
| [wstunnel](https://github.com/erebe/wstunnel) | 以 WebSocket 或 HTTP/2 为传输层的 TCP、UDP 和 Unix Socket 隧道工具。 | websocket、http2、tcp、udp、mtls | BSD-3-Clause | 7,114 | v11.0.0 | 92.5 | 2026-09-09 |
| [sish](https://github.com/antoniomika/sish) | 基于标准 SSH 反向转发提供 HTTP、HTTPS、WebSocket、TCP 和 SNI 隧道的自托管服务。 | ssh、http、tcp、websocket、sni | MIT | 4,791 | v2.24.1 | 91.3 | 2026-09-09 |
| [zrok](https://github.com/openziti/zrok) | 基于 OpenZiti 的安全资源分享与隧道工具，可公开或私密共享 Web、TCP、UDP 和文件资源。 | http、tcp、udp、openziti、self-hosted | Apache-2.0 | 4,780 | v2.0.8 | 90.9 | 2026-09-09 |
| [GOST](https://github.com/go-gost/gost) | 支持多种传输协议、转发链、反向代理和 TCP/UDP 内网穿透的通用隧道工具。 | tcp、udp、websocket、quic、reverse-proxy | MIT | 7,662 | v3.3.0 | 90.7 | 2026-09-09 |
| [Expose](https://github.com/exposedev/expose) | 使用 PHP 构建的开源 HTTP 隧道服务，支持自托管服务端和本地应用公开。 | http、php、self-hosted、development、tunnel-server | MIT | 4,573 | 3.2.4 | 88.8 | 2026-09-09 |
| [rathole](https://github.com/rathole-org/rathole) | 使用 Rust 实现的轻量反向隧道，面向将 NAT 后的 TCP 服务映射到公网服务器。 | tcp、tls、noise、rust、nat-traversal | Apache-2.0 | 14,351 | v0.5.0 | 76.1 | 2026-09-09 |
| [bore](https://github.com/ekzhang/bore) | 用 Rust 编写的简洁 TCP 隧道，可将本地端口经自托管远端服务器公开。 | tcp、rust、self-hosted、nat-traversal | MIT | 11,538 | v0.6.0 | 72.2 | 2026-09-09 |

## 零信任访问入口

| 项目 | 客观简介 | 标签 | License | Star | 最新 Release | 信号分 | 最后复核日 |
|---|---|---|---|---:|---|---:|---|
| [OAuth2 Proxy](https://github.com/oauth2-proxy/oauth2-proxy) | 在上游应用前通过 OAuth 2.0 或 OpenID Connect 身份提供商执行认证的反向代理。 | oauth2、oidc、sso、forward-auth、http | MIT | 15,212 | v7.15.5 | 95.1 | 2026-09-09 |
| [Pomerium](https://github.com/pomerium/pomerium) | 面向内部 Web 应用和服务的身份与上下文感知反向代理，可按策略验证每次访问。 | identity-aware-proxy、oidc、policy、http、beyondcorp | Apache-2.0 | 5,051 | v0.33.4 | 91.4 | 2026-09-09 |

## 反代管理面板

| 项目 | 客观简介 | 标签 | License | Star | 最新 Release | 信号分 | 最后复核日 |
|---|---|---|---|---:|---|---:|---|
| [Nginx Proxy Manager](https://github.com/NginxProxyManager/nginx-proxy-manager) | 通过 Web 界面管理 Nginx 代理主机、重定向、TCP/UDP 流和 TLS 证书的容器化工具。 | nginx、webui、letsencrypt、docker、tcp | MIT | 34,447 | v2.16.0 | 97.2 | 2026-09-09 |
| [Nginx UI](https://github.com/0xJacky/nginx-ui) | 用于编辑、验证和发布 Nginx 配置，并管理证书、日志和运行状态的跨平台 Web 管理界面。 | nginx、webui、configuration、letsencrypt、monitoring | AGPL-3.0 | 11,645 | v2.9.0 | 93.8 | 2026-09-09 |
| [BunkerWeb](https://github.com/bunkerity/bunkerweb) | 基于 Nginx 的反向代理与 Web 应用防火墙平台，提供 Web 界面、自动配置和多种部署方式。 | nginx、waf、webui、security、kubernetes | AGPL-3.0 | 11,084 | v1.6.16 | 93.4 | 2026-09-09 |
| [Zoraxy](https://github.com/tobychui/zoraxy) | 自带 Web 管理界面的通用 HTTP 反向代理与 TCP/UDP 转发工具。 | webui、http、tcp、udp、access-control | AGPL-3.0 | 5,527 | v3.3.5-rc3 | 91.5 | 2026-09-09 |

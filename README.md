# GFWlist

个人维护的补充网络规则，可供 Mihomo/Stash 的 `classical` 规则集，以及 Surge、Shadowrocket 的远程规则集使用。

## 规则文件

| 文件 | 用途 | Raw 地址 |
| --- | --- | --- |
| `Directlist.list` | 需要直连的补充规则 | `https://raw.githubusercontent.com/ordinaryzzyy/GFWlist/main/Directlist.list` |
| `GFWlist.list` | 需要代理的补充规则 | `https://raw.githubusercontent.com/ordinaryzzyy/GFWlist/main/GFWlist.list` |
| `Rejectlist.list` | 需要拒绝的补充规则 | `https://raw.githubusercontent.com/ordinaryzzyy/GFWlist/main/Rejectlist.list` |

这些文件是针对现有规则集的增量补充，不是完整的分流方案。使用时应确保拒绝和直连规则位于兜底代理规则之前。

## Mihomo 示例

```yaml
rule-providers:
  personal-direct:
    type: http
    behavior: classical
    format: text
    url: https://raw.githubusercontent.com/ordinaryzzyy/GFWlist/main/Directlist.list
    path: ./ruleset/personal-direct.list
    interval: 86400

  personal-proxy:
    type: http
    behavior: classical
    format: text
    url: https://raw.githubusercontent.com/ordinaryzzyy/GFWlist/main/GFWlist.list
    path: ./ruleset/personal-proxy.list
    interval: 86400

  personal-reject:
    type: http
    behavior: classical
    format: text
    url: https://raw.githubusercontent.com/ordinaryzzyy/GFWlist/main/Rejectlist.list
    path: ./ruleset/personal-reject.list
    interval: 86400

rules:
  - RULE-SET,personal-reject,REJECT
  - RULE-SET,personal-direct,DIRECT
  - RULE-SET,personal-proxy,PROXY
```

请把示例中的 `PROXY` 替换为配置里实际存在的策略组名称。

## 维护约定

- 每行只放一条规则，规则值使用小写。
- 域名优先使用 `DOMAIN-SUFFIX`；只有确需匹配单一主机时才使用 `DOMAIN`。
- 新增规则时写明分类；无法确认的临时条目放在 `UNKNOWN` 下。
- 不因域名暂时无法解析就直接删除规则，删除前应确认其业务归属和实际流量。
- 同一条规则不得重复，也不得同时出现在直连和代理列表中。
- 修改规则后运行 `python3 scripts/validate_rules.py`。

## 支持的规则类型

`DOMAIN`、`DOMAIN-SUFFIX`、`DOMAIN-KEYWORD`、`IP-CIDR`、`IP-CIDR6` 和 `IP-ASN`。可在 IP 类规则末尾附加 `no-resolve`。

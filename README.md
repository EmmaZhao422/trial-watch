# Trial Watch · 竞品临床试验情报 Agent（Alpha）

Emma Zhao（Duke）的求职作品项目。网站展示：每天自动更新的竞品试验关注名单、Agent 写的变化简报、工作原理和 Alpha 评测。

## 文件说明

| 文件 | 作用 |
|---|---|
| `index.html` | 网站本体（一个页面，读取同目录里的数据文件） |
| `briefs.json` | Agent 生成的简报（文字照原样，不要改写） |
| `watchlist_config.json` | 关注名单：要跟踪哪些试验。增删试验只改这里 |
| `watchlist.json` | 网站显示的最新试验数据（由自动任务生成） |
| `snapshots/` | 每天一份快照，之后用 SQL 做变化检测的原材料 |
| `update_watchlist.py` | 从 ClinicalTrials.gov API 拉数据（只用 Python 标准库） |
| `.github/workflows/update-and-deploy.yml` | 每天自动拉数据 + 发布网站；推送代码时也会发布 |

## 上线步骤（给执行的 AI / Emma）

1. 在 GitHub 新建 **Public** 仓库，名字 `trial-watch`。把本文件夹里**所有**文件原样上传，包括隐藏文件夹 `.github`（Mac 的 Finder 默认看不到它：按 `Cmd + Shift + .` 显示；或者在网页上用 Add file → Create new file，路径填 `.github/workflows/update-and-deploy.yml`，粘贴内容）。
2. 仓库 Settings → Pages → Build and deployment → Source 选 **GitHub Actions**。
3. Settings → Actions → General → Workflow permissions 选 **Read and write permissions**，保存。
4. 打开 Actions 标签 → 左侧 “Update watchlist and deploy” → **Run workflow**。等它变绿（约 1–2 分钟）。
5. 网址是 `https://<GitHub用户名>.github.io/trial-watch/`。用无痕窗口打开，检查：
   - 「本周简报」显示 3 张卡片（#1 显示“人工基准撰写中”，#2、#3 有四段内容）
   - 「关注名单」显示 8 个试验，右上角写着“每天自动更新 · 最近一次：……”（不再是 10-20）
   - 「查询任意试验」输入 NCT07533175 能查到结果；如果显示“浏览器拦截了跨站请求”，记下来即可，不影响其他部分
6. 如果第 4 步失败：打开失败的那一步，把报错原文发给 Emma，不要自行删功能。

## 自定义域名（可选，github.io 网址今晚就能用）

GitHub 学生包里 Namecheap 送一年 `.me` 域名。
1. 在 Namecheap 领取域名（例如 `emmazhao.me`）。
2. Namecheap → Domain List → Manage → Advanced DNS，添加一条记录：类型 `CNAME`，Host `trials`，Value `<GitHub用户名>.github.io`。
3. GitHub 仓库 Settings → Pages → Custom domain 填 `trials.emmazhao.me`，保存；DNS 检查通过后勾选 **Enforce HTTPS**。
4. DNS 生效可能要几分钟到几小时。生效前先把 github.io 网址发给老师。

## 规则（改网站时必须遵守）

- `briefs.json` 里 Agent 的文字不改写、不润色、不补充。
- 不添加任何没做到的功能或成果描述（例如“准确率 xx%”“网站可一键运行 Agent”）。
- Emma 核对完某条简报后，只把该变化的 `"verification"` 从 `"unverified"` 改为 `"verified"`。
- 不在网页或仓库里放任何 API 密钥、密码或个人联系方式。

# 随机练习 API 部署说明

题库放在**私密 GitHub 仓库**，通过 Cloudflare Worker 按需返回单题。公开主页仓库只包含练习页面，不包含 `questions.json`。

## 1. 创建私密题库仓库

在 GitHub 新建 **Private** 仓库，例如 `analysis-algebra`，只提交：

- `questions.json`
- （可选）`markdown/` 目录

**不要**把题库放进 `Y-D-1.github.io` 公开仓库。

本地首次推送示例：

```bash
bash scripts/prepare_practice_data_repo.sh
cd ~/suncoastmath-data
git remote add origin git@github.com:Y-D-1/analysis-algebra.git
git push -u origin main
```

## 2. 配置 Cloudflare

### 2.1 注册并进入 Workers

1. 打开 [Cloudflare Dashboard](https://dash.cloudflare.com/) 并登录（用邮箱注册即可，**不必购买域名**）
2. 左侧边栏找 **Workers & Pages**；若没有，在左侧搜索框输入 `Workers`
3. 首次进入可能提示启用 Workers，点 **Get started** / **开始使用**（免费）

### 2.2 创建 KV（新版界面叫「实例」）

KV 现在是独立页面，不一定在 Workers 子菜单里。

**方法一：直接打开**

https://dash.cloudflare.com/?to=/:account/workers/kv/namespaces

**方法二：从左侧菜单**

左侧 **Workers KV**（或 **Storage & databases** → **Workers KV**）→ **Create instance**（创建实例）

- 名称填：`yudongyi-practice`
- 创建后点进该实例，在 **Settings** 或概览页复制 **Namespace ID**（一长串十六进制）

### 2.3 创建 API Token

1. 右上角头像 → **My Profile**（我的资料）
2. 左侧 **API Tokens** → **Create Token**
3. 可用模板 **Edit Cloudflare Workers**，或自定义权限：
   - Account → **Workers KV Storage** → Edit
   - Account → **Workers Scripts** → Edit
4. 创建后**只显示一次**，请复制保存

### 2.4 查 Account ID

回到 [Workers & Pages](https://dash.cloudflare.com/?to=/:account/workers-and-pages) 概览页，右侧 **Account ID** 可复制。

### 若仍找不到 KV

- 确认登录的是 **个人账号**，不是别人邀你进的只读团队
- 左侧搜索 `KV` 或 `Workers KV`
- 换电脑浏览器试（手机版常缺菜单）
- 或用命令行创建（需本机安装 [Node.js](https://nodejs.org/)）：

```bash
cd worker
npm install
npx wrangler login
npx wrangler kv namespace create QUESTIONS
```

终端会输出 `id: "xxxxxxxx"`，这就是 `CLOUDFLARE_KV_NAMESPACE_ID`。

## 3. 在公开仓库添加 GitHub Secrets

打开 `Y-D-1/Y-D-1.github.io` → **Settings** → **Secrets and variables** → **Actions**，添加：

| Secret | 说明 |
|--------|------|
| `CLOUDFLARE_API_TOKEN` | 上一步创建的 Token |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare 账户 ID（Dashboard 右侧） |
| `CLOUDFLARE_KV_NAMESPACE_ID` | KV Namespace ID |
| `DATA_REPO_PAT` | GitHub PAT，`repo` 权限，用于读取私密题库仓库 |
| `PRACTICE_DATA_REPO` | 私密仓库名，如 `Y-D-1/analysis-algebra` |

创建 PAT：GitHub → Settings → Developer settings → Personal access tokens。

## 4. 部署 Worker 并同步题库

将本仓库改动 push 到 `master` 后：

1. **Actions** → **Deploy practice API** → **Run workflow**（部署 Worker）
2. 在 Workers 页面记下 Worker 地址，形如 `https://yudongyi-practice.<子域>.workers.dev`
3. 编辑 `_data/practice.yml`，填入 `api_base`（无末尾斜杠），commit 并 push
4. **Actions** → **Sync practice data** → **Run workflow**（上传题库到 KV）

## 5. 本地开发

```bash
python3 scripts/build_practice_kv.py \
  --input /path/to/questions.json \
  --output kv-bulk.json

cd worker
npm install
npx wrangler dev
```

本地 Jekyll 预览时，`ALLOWED_ORIGINS` 已包含 `http://localhost:4000`。

## API 接口

- `GET /api/meta` — 科目、难度、题量统计
- `GET /api/random?subject=数学分析&difficulty=3` — 随机一题（不含解析）
- `GET /api/solution?id=<题目ID>` — 获取解析

## 更新题库

更新私密仓库中的 `questions.json` 后，在公开仓库手动运行 **Sync practice data** workflow 即可。

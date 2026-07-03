# GitHub 上传说明

本仓库默认不提交：

- `.env` 和任何真实密钥。
- GPU 云实例密码。
- 本地 `.vscode/`。
- 原始 `.docx` 二进制草稿。
- `results/` 下的实验输出。

## 已有 GitHub 空仓库

```bash
git remote add origin git@github.com:<your-name>/llm-elastic-governor.git
git branch -M main
git push -u origin main
```

## 使用 HTTPS remote

```bash
git remote add origin https://github.com/<your-name>/llm-elastic-governor.git
git branch -M main
git push -u origin main
```

如果 GitHub 要求认证，使用 browser login、SSH key 或 Personal Access Token。不要把 token 写进仓库文件。

## 安装 GitHub CLI 后创建仓库

```bash
gh auth login
gh repo create llm-elastic-governor --public --source . --remote origin --push
```


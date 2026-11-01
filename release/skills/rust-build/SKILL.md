---
name: rust-build
description: Rust/Cargo 编译通用 skill。触发词："cargo build"、"编译 rust"、"build release"、"cargo 编译"。支持 GNU 工具链、Tauri 项目、常见编译问题诊断。
---

# rust-build

Rust 项目编译通用指南，适用于任何 Cargo 项目（包括 Tauri）。

## 基础编译命令

```bash
# 进入项目目录（含 Cargo.toml）
cd <project_path>

# Debug 编译（快速，用于开发）
cargo build

# Release 编译（优化，用于发布）
cargo build --release

# 检查编译错误（不生成二进制，最快）
cargo check

# 运行
cargo run [--release]
```

## Tauri 项目编译

### 仅编译可执行文件

```bash
cd <project>/src-tauri

# 如果项目路径包含空格，GNU toolchain 的 dlltool.exe 可能处理失败，
# 请从 junction 路径（如 C:\CODE\typora-next）进入再编译。
cargo build --release
```

输出位置：`src-tauri/target/release/`

### 打包安装包（MSI + NSIS）

```bash
cd <project>/src-tauri

# 必须将 MinGW windres 加入 PATH，否则打包会报错 "windres program not found"
export PATH="/c/Users/17625/scoop/apps/mingw/15.2.0-rt_v13-rev0/bin:$PATH"

# cargo tauri build 内部会先执行 cargo build --release，无需提前手动运行。
cargo tauri build
```

输出位置（具体文件名以 `tauri.conf.json` / `Cargo.toml` 中的版本为准）：
- MSI: `src-tauri/target/release/bundle/msi/<crate_name>_<version>_x64_en-US.msi`
- NSIS: `src-tauri/target/release/bundle/nsis/<crate_name>_<version>_x64-setup.exe`

> 注意：`cargo tauri build` 内部会先执行 `cargo build --release`，再调用 WiX/NSIS 打包工具。首次打包会自动下载 WiX Toolset，无需手动安装。

## 编译产物位置

- Debug: `target/debug/<crate_name>.exe`
- Release: `target/release/<crate_name>.exe`

查看产物：
```bash
ls -la target/release/<crate_name>.exe
```

## Tauri Release 模式注意事项

Release 模式下，Tauri 会在编译时将 `dist/` 目录的前端资源嵌入 exe。修改 `dist/` 后，**必须重新完整编译**（`cargo clean` + `cargo build --release`），单纯的增量编译不会重新嵌入资源。

验证发布版本是否生效：
1. `ls -lh target/release/<crate_name>.exe` 确认文件存在
2. `stat target/release/<crate_name>.exe` 确认时间戳是刚编译的
3. 手动启动应用确认变更生效

## GNU 工具链配置 (Windows)

用户环境使用 `stable-x86_64-pc-windows-gnu` 工具链：

```bash
# 先检查当前工具链
rustup show

# 如果不是 GNU 工具链，再切换
rustup default stable-x86_64-pc-windows-gnu

# MinGW PATH（编译和打包都需要）
export PATH="/c/Users/17625/scoop/apps/mingw/15.2.0-rt_v13-rev0/bin:$PATH"
```

## 常见编译选项

| 选项 | 说明 |
|------|------|
| `--release` | 优化编译，生产发布 |
| `--features <feat>` | 启用指定 feature |
| `--no-default-features` | 禁用默认 features |
| `--target <triple>` | 交叉编译目标平台 |
| `--jobs <n>` | 并行编译线程数 |
| `-vv` | 详细输出（调试用） |

## 清理命令

```bash
# 清理编译产物
cargo clean

# 清理并重编（Windows Git Bash 下使用 ; 而非 &&）
cargo clean ; cargo build --release
```

## 常见问题诊断

| 问题 | 诊断/解决方案 |
|------|--------------|
| "can't find crate for `std`" | 工具链问题：`rustup default stable-x86_64-pc-windows-gnu` |
| "linking with `link.exe` failed" | Git Bash 的 `/usr/bin/link.exe` 干扰，确认 GNU 工具链 |
| "dlltool not found" | MinGW PATH 未生效，执行上方 export 命令或检查 scoop 安装 |
| "windres program not found" | 同上，打包安装包时需要 windres |
| 编译卡住/慢 | `cargo clean` 清理后重试，检查 CPU/内存占用 |
| 依赖下载慢 | 配置 cargo 镜像源 `~/.cargo/config.toml` |
| release 后前端显示 localhost 拒绝连接 | Tauri 配置或前端代码指向了 dev server；检查 `tauri.conf.json` 的 `windows.url` / `build.frontendDist`，确认 `dist/` 已嵌入，前端无硬编码 `http://localhost` 调用 |

## 编译检查清单

编译前确认：
1. 在含 `Cargo.toml` 的目录执行
2. 工具链正确（`rustup show`）
3. 依赖已下载（`cargo fetch` 或首次编译自动下载）
4. 代码格式：`cargo fmt`
5. 静态检查：`cargo clippy`
6. 若项目有前端测试（如 typora-next 的 `tests/unit`、`tests/bdd-acceptance`），先跑 JS 测试

编译后验证：
1. 检查 `target/release/*.exe` 是否生成
2. 检查产物时间戳，确认是刚编译的
3. 运行测试：`cargo test [--release]`
4. 若是 Tauri 项目，手动启动 exe 确认前端正常加载
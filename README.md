<div align="center">

# KiramiCLI

✨ KiramiBot 命令行工具 ✨

</div>

<p align="center">
    <a href="https://raw.githubusercontent.com/A-kirami/KiramiCLI/main/LICENSE">
        <img src="https://img.shields.io/github/license/A-kirami/KiramiCLI" alt="license">
    </a>
    <a href="https://pypi.python.org/pypi/kirami-cli">
        <img src="https://img.shields.io/pypi/v/kirami-cli" alt="pypi">
    </a>
    <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=edb641" alt="python">
    <a href="https://github.com/psf/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?logo=python&logoColor=edb641" alt="black">
    </a>
    <a href="https://github.com/Microsoft/pyright">
    <img src="https://img.shields.io/badge/types-pyright-797952.svg?logo=python&logoColor=edb641" alt="pyright">
    </a>
    <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json" alt="ruff">
    </a>
    <br />
    <a href="https://results.pre-commit.ci/latest/github/A-kirami/KiramiCLI/main">
      <img src="https://results.pre-commit.ci/badge/github/A-kirami/KiramiCLI/main.svg" alt="pre-commit" />
    </a>
    <a href="https://github.com/A-kirami/KiramiCLI/actions/workflows/pyright.yml">
      <img src="https://github.com/A-kirami/KiramiCLI/actions/workflows/pyright.yml/badge.svg?branch=main&event=push" alt="pyright">
    </a>
    <a href="https://github.com/A-kirami/KiramiCLI/actions/workflows/ruff.yml">
      <img src="https://github.com/A-kirami/KiramiCLI/actions/workflows/ruff.yml/badge.svg?branch=main&event=push" alt="ruff">
    </a>
</p>

<p align="center">
    <a href="https://cli.kiramibot.dev/" target="__blank">文档</a>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="https://cli.kiramibot.dev/docs/guide/installation" target="__blank">安装</a>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="https://kiramibot.dev/" target="__blank">KiramiBot 文档</a>
</p>

## 功能

- 创建新的 KiramiBot 项目
- 启动 KiramiBot
- 管理插件
  - 创建新的插件
  - 搜索/安装/更新/卸载在官方商店上发布的插件
- 管理适配器
  - 创建新的适配器
  - 搜索/安装/更新/卸载在官方商店上发布的适配器
- 管理驱动器
  - 搜索/安装/更新/卸载在官方商店上发布的驱动器
- 从 NoneBot2 迁移到 KiramiBot
- 支持 CLI 插件和运行脚本

## 安装

### 推荐安装方式

#### Linux, macOS, Windows (WSL)

```bash
curl -sSL https://install.kiramibot.dev | python3 -
```

#### Windows (Powershell)

```powershell
(Invoke-WebRequest -Uri https://install.kiramibot.dev -UseBasicParsing).Content | py -
```

### 其他安装方式

#### pipx

```shell
pipx install kirami-cli
```

#### pip

```shell
pip install --user kirami-cli
```

## 使用

完整使用说明请参考 [文档](https://cli.kiramibot.dev/)。

### 命令行使用

```shell
kirami --help
```

> [!WARNING]
> 如果找不到 `kirami` 命令，请尝试 `pipx ensurepath` 来添加路径到环境变量

- `kirami create (init)` 创建新的 KiramiBot 项目
- `kirami run` 在当前目录启动 KiramiBot
- `kirami driver` 管理驱动器
- `kirami plugin` 管理插件
- `kirami adapter` 管理适配器
- `kirami self` 管理 CLI 内部环境
- `kirami migrate` 从 NoneBot2 迁移到 KiramiBot
- `kirami <script>` 运行脚本

### 交互式使用

```shell
kirami
```

## 开发

### 翻译

生成模板

```shell
pdm run extract
```

初始化语言翻译文件或者更新现有语言翻译文件

```shell
pdm run init en_US
```

更新语言翻译文件

```shell
pdm run update
```

编译语言翻译文件

```shell
pdm run compile
```

## 许可证

本项目原始代码来自 [NB CLI](https://github.com/nonebot/nb-cli)，以相同的许可证发布。

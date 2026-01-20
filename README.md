# Urban Energy Resilience

> 中国城市能源系统韧性研究 —— 基于复杂网络分析

## 项目概述

本项目采用复杂网络分析方法，研究中国城市能源系统的抗干扰能力和韧性。通过建立三级响应韧性评估体系（经济、人口、结构），分析六大区域电网（华北、东北、华东、华中、西北、南方）在2001-2020年间的能源系统韧性特征。

### 核心研究框架

```
┌─────────────────────────────────────────────────────────────┐
│                   城市能源系统韧性评估体系                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  一级响应（经济）          二级响应（社会）      三级响应（结构） │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐│
│  │ 经济富裕度    │    │ 人均能耗富裕度 │    │ 集成影响力CI  ││
│  │ 能源投资比例  │    │ 人口因素      │    │ 网络结构      ││
│  │ 能耗富裕度    │    │ 主动降负荷能力 │    │ 节点重要性    ││
│  └───────────────┘    └───────────────┘    └───────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```
Urban-energy-resilience/
│
├── README.md              # 项目说明
├── requirements.txt       # Python依赖
├── .gitignore            # Git忽略规则
│
├── config/
│   └── config.yaml       # 项目配置文件
│
├── data/
│   ├── raw/              # 原始数据（只读）
│   ├── processed/        # 预处理后的中间数据
│   └── external/         # 新增数据源
│
├── src/                  # 源代码
│   ├── preprocessing/    # 网络数据预处理
│   ├── network_analysis/ # 网络结构分析
│   ├── resilience/       # 韧性分析核心
│   ├── attack_simulation/# 攻击-恢复模拟
│   ├── validation/       # 数据验证
│   └── visualization/    # 结果可视化
│
├── scripts/              # 主流程脚本
│   ├── run_pipeline.py   # 完整流程入口
│   ├── run_attack_recovery.py
│   └── run_analysis.py
│
├── notebooks/            # 探索性分析
│
├── outputs/              # 输出结果
│   ├── figures/          # 图表
│   ├── tables/           # 数据表
│   └── results/          # 分析结果
│
├── tests/                # 单元测试
│
└── venv/                 # 虚拟环境
```

## 快速开始

### 1. 环境设置

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据准备

将原始数据文件放入 `data/raw/` 目录：
- `all_networks.pkl` - 能源网络结构
- `env_vars.pkl` - 节点分类数据
- `env_GDP_Population.pkl` - GDP和人口数据

### 3. 运行分析

```bash
# 运行完整分析流程
python scripts/run_pipeline.py --level all

# 运行攻击-恢复模拟
python scripts/run_attack_recovery.py --n-simulations 1000

# 运行特定级别韧性计算
python scripts/run_analysis.py --level 1 --years 2015 2020
```

## 核心算法

### 1. 集成影响力 (Collective Influence, CI)

计算节点在网络中的综合重要性，用于评估能源网络中各节点的战略地位。

### 2. 随机攻击-恢复模拟

采用Bootstrap方法，模拟网络边随机删除后的系统响应和恢复过程，评估网络的抗干扰能力。

### 3. NCI指数

综合网络复杂指数，基于熵权-TOPSIS方法计算，用于量化网络结构的复杂性。

## 研究对象

| 区域电网 | 覆盖范围 |
|---------|---------|
| 华北 | 北京、天津、河北、山西、山东 |
| 东北 | 辽宁、吉林、黑龙江 |
| 华东 | 上海、江苏、浙江、安徽、福建 |
| 华中 | 河南、湖北、湖南、江西 |
| 西北 | 陕西、甘肃、青海、宁夏、新疆 |
| 南方 | 广东、广西、云南、贵州、海南 |

## 配置说明

项目配置文件 `config/config.yaml` 包含：

- 路径配置
- 数据文件配置
- 研究参数（年份、区域）
- 攻击-恢复模拟参数
- 韧性指标权重
- 计算配置（并行、随机种子）
- 可视化配置
- 日志配置

## 性能优化

项目使用多进程并行计算，默认配置为16进程，比单线程快约10倍。可在 `config.yaml` 中调整 `n_processes` 参数。

## 版本控制

使用 Git 进行版本管理：

```bash
# 初始化仓库
git init

# 添加文件
git add .

# 提交
git commit -m "Initial project structure"
```

## 开发进度

- [x] Phase 1: 项目骨架 + 配置管理
- [ ] Phase 2: 迁移预处理模块
- [ ] Phase 3: 迁移核心计算模块
- [ ] Phase 4: 建立主流程
- [ ] Phase 5: Git 初始化

## 许可证

本研究项目仅用于学术研究目的。

## 联系方式

如有问题或建议，请联系项目维护者。

# 工程预算管理系统

一个基于Flask和HTML的工程预算管理系统，支持用户认证、项目管理和预算创建功能。

## 功能特性

### 后端功能
- **用户认证**：登录/登出功能，基于session的身份验证
- **项目管理**：获取项目列表
- **预算管理**：创建预算、获取预算详情
- **数据模型**：用户、项目、预算、预算明细
- **管理后台**：基于Flask-Admin的后台管理界面，用于数据维护。

### 前端功能
- **响应式设计**：使用Tailwind CSS构建的现代化界面
- **用户登录**：支持多角色用户登录
- **预算表单**：动态添加材料明细，实时计算金额
- **数据可视化**：使用Chart.js展示预算构成
- **交互体验**：流畅的动画和用户反馈

## 系统要求

- Python 3.8 或更高版本
- 现代浏览器（Chrome、Firefox、Safari、Edge）

## 快速开始

### 方法一：使用启动脚本（推荐）

1. 双击运行 `start.bat` 文件
2. 等待依赖安装完成和服务启动
3. 在浏览器中打开 `index.html` 文件

### 方法二：手动启动

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **启动后端服务**
   ```bash
   python budget-b.py
   ```

3. **打开前端界面**
   - 在浏览器中打开 `index.html` 文件
   - 或者访问 `file:///path/to/index.html`

## 测试账号

系统预置了以下测试账号：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 领导 |
| budgeter | budgeter123 | 预算员 |
| manager | manager123 | 项目经理 |

## 使用说明

1. **登录系统**
   - 使用上述测试账号登录
   - 登录成功后会显示主界面

2. **创建预算 (预算员角色)**
   - 使用 `budgeter` 账号登录。
   - 选择项目。
   - 添加材料明细（材料名称、规格、数量、单价等）。
   - 系统会自动计算总金额。
   - 提交预算等待审批。

3. **审批预算与数据管理 (领导/项目经理角色)**
   - 使用 `admin` 或 `manager` 账号登录。
   - 访问管理后台：后端服务启动后，在浏览器中打开 `http://localhost:5001/admin` (具体端口请参照后端服务启动时的输出)。
   - 在管理后台中，可以管理用户、项目、预算及预算明细。包括查看、创建、修改和删除数据。
   - 预算审批：领导或项目经理可以在预算管理模块修改预算状态（如：待审批 -> 已审批/已驳回）。

4. **查看数据 (前端)**
   - 前端界面会根据用户角色和预算状态展示相应数据。
   - 预算总额实时更新。
   - 图表显示预算构成分析。

## 项目结构

```
工程预算管理系统/
├── budget-b.py          # Flask后端应用 (包含 /admin 后台管理)
├── index.html           # 前端用户界面
├── requirements.txt     # Python依赖
├── start.bat            # Windows启动脚本
├── README.md            # 说明文档
└── budget_management.db # SQLite数据库（运行后自动生成）
```
* `backend-dashboard.html` 文件已废弃，请使用 `/admin` 路径访问由Flask-Admin提供的管理后台。

## API接口

### 用户认证
- `POST /api/login` - 用户登录
- `POST /api/logout` - 用户登出

### 项目管理
- `GET /api/projects` - 获取项目列表

### 预算管理
- `POST /api/budgets` - 创建预算
- `GET /api/budgets/<id>` - 获取预算详情

## 技术栈

### 后端
- **Flask** - Web框架
- **SQLAlchemy** - ORM数据库操作
- **Flask-Admin** - 后台管理界面框架
- **Flask-CORS** - 跨域支持
- **SQLite** - 数据库

### 前端
- **HTML5/CSS3** - 基础结构和样式
- **Tailwind CSS** - 样式框架
- **JavaScript** - 交互逻辑
- **Chart.js** - 图表库
- **Font Awesome** - 图标库

## 注意事项

1. **数据库**：首次运行会自动创建SQLite数据库和测试数据
2. **端口**：后端服务默认运行在5000端口
3. **CORS**：已配置跨域支持，前端可以正常调用后端API
4. **浏览器**：建议使用现代浏览器以获得最佳体验

## 故障排除

### 常见问题

1. **Python未找到**
   - 确保已安装Python 3.8+
   - 检查Python是否添加到系统PATH

2. **依赖安装失败**
   - 尝试升级pip：`python -m pip install --upgrade pip`
   - 使用国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`

3. **前端无法连接后端**
   - 确保后端服务正在运行
   - 检查浏览器控制台是否有错误信息
   - 确认API地址是否正确（默认：http://localhost:5000）

4. **登录失败**
   - 检查用户名和密码是否正确
   - 确认后端服务正常运行
   - 查看浏览器网络请求是否成功

## 开发说明

如需进一步开发，可以：

1. **扩展功能**：在Flask应用中添加新的API接口
2. **优化界面**：修改HTML和CSS样式
3. **数据库**：可以替换为MySQL、PostgreSQL等数据库
4. **部署**：可以部署到云服务器或容器中

## 许可证

本项目仅供学习和演示使用。

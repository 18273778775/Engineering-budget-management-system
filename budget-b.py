from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget_management.db'  # 使用SQLite便于演示
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 启用CORS以允许前端调用
# 明确指定允许的源地址，确保localhost和127.0.0.1都能正常访问
CORS(app,
     supports_credentials=True,
     origins=[
         'http://localhost:5001',
         'http://127.0.0.1:5001',
         'file://',  # 支持直接打开HTML文件
         'null'      # 支持本地文件访问
     ],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     expose_headers=['Content-Type', 'Authorization'])

db = SQLAlchemy(app)

# 数据模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 预算员、项目经理、领导
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manager = db.relationship('User', backref='managed_projects')

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    create_time = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    status = db.Column(db.String(20), default='草稿')  # 草稿、待审批、已审批、已驳回
    total_amount = db.Column(db.Float, nullable=False, default=0)
    
    project = db.relationship('Project', backref='budgets')
    creator = db.relationship('User', backref='created_budgets')
    details = db.relationship('BudgetDetail', backref='budget', lazy=True, cascade="all, delete-orphan")

class BudgetDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False, default='材料')  # 材料、人工、设备、其他
    item_name = db.Column(db.String(100), nullable=False)
    specification = db.Column(db.String(100))
    unit = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)

# 静态文件和页面路由
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api')
def api_info():
    return jsonify({'message': '工程预算管理系统API', 'status': 'running'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['role'] = user.role
        return jsonify({
            'message': '登录成功',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        }), 200
    else:
        return jsonify({'message': '用户名或密码错误'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return jsonify({'message': '登出成功'}), 200

@app.route('/api/projects', methods=['GET'])
def get_projects():
    if 'user_id' not in session:
        return jsonify({'message': '请先登录'}), 401
    
    projects = Project.query.all()
    result = []
    for project in projects:
        result.append({
            'id': project.id,
            'name': project.name,
            'start_date': project.start_date.strftime('%Y-%m-%d'),
            'manager': project.manager.username
        })
    return jsonify(result), 200

@app.route('/api/projects', methods=['POST'])
def create_project():
    if 'user_id' not in session:
        return jsonify({'message': '请先登录'}), 401

    data = request.json
    project_name = data.get('name', '').strip()
    start_date_str = data.get('start_date', '')

    if not project_name:
        return jsonify({'message': '项目名称不能为空'}), 400

    # 检查项目名称是否已存在
    existing_project = Project.query.filter_by(name=project_name).first()
    if existing_project:
        return jsonify({'message': '项目名称已存在'}), 400

    try:
        # 解析开始日期
        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.datetime.now()

        # 获取当前用户作为项目经理（如果是项目经理角色）或使用默认项目经理
        current_user = User.query.get(session['user_id'])
        if current_user.role == '项目经理':
            manager = current_user
        else:
            # 使用默认的项目经理（ID为3）
            manager = User.query.filter_by(role='项目经理').first()
            if not manager:
                manager = current_user  # 如果没有项目经理，使用当前用户

        # 创建新项目
        new_project = Project(
            name=project_name,
            start_date=start_date,
            manager=manager
        )

        db.session.add(new_project)
        db.session.commit()

        return jsonify({
            'message': '项目创建成功',
            'id': new_project.id,
            'name': new_project.name,
            'start_date': new_project.start_date.strftime('%Y-%m-%d'),
            'manager': new_project.manager.username
        }), 201

    except ValueError:
        return jsonify({'message': '日期格式错误，请使用YYYY-MM-DD格式'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'创建项目失败: {str(e)}'}), 500

@app.route('/api/budgets', methods=['POST'])
def create_budget():
    if 'user_id' not in session:
        return jsonify({'message': '请先登录'}), 401
    
    data = request.json
    project_id = data.get('project_id')
    details = data.get('details', [])
    
    if not project_id:
        return jsonify({'message': '项目ID不能为空'}), 400
    
    if not details or len(details) == 0:
        return jsonify({'message': '预算明细不能为空'}), 400
    
    # 计算总金额
    total_amount = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in details)
    
    # 创建预算
    new_budget = Budget(
        project_id=project_id,
        creator_id=session['user_id'],
        status='待审批',
        total_amount=total_amount
    )
    
    # 添加明细
    for item in details:
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        amount = quantity * unit_price

        detail = BudgetDetail(
            budget=new_budget,
            item_type=item.get('item_type', '材料'),
            item_name=item.get('item_name', item.get('material_name', '')),  # 兼容旧字段
            specification=item.get('specification', ''),
            unit=item.get('unit', ''),
            quantity=quantity,
            unit_price=unit_price,
            amount=amount
        )
        db.session.add(detail)
    
    db.session.add(new_budget)
    db.session.commit()
    
    return jsonify({
        'message': '预算创建成功',
        'budget_id': new_budget.id
    }), 201

@app.route('/api/budgets/<int:budget_id>', methods=['GET'])
def get_budget(budget_id):
    if 'user_id' not in session:
        return jsonify({'message': '请先登录'}), 401
    
    budget = Budget.query.get_or_404(budget_id)
    
    result = {
        'id': budget.id,
        'project_id': budget.project_id,
        'project_name': budget.project.name,
        'creator_id': budget.creator_id,
        'creator_name': budget.creator.username,
        'create_time': budget.create_time.strftime('%Y-%m-%d %H:%M:%S'),
        'status': budget.status,
        'total_amount': budget.total_amount,
        'details': []
    }
    
    for detail in budget.details:
        result['details'].append({
            'id': detail.id,
            'item_type': detail.item_type,
            'item_name': detail.item_name,
            'specification': detail.specification,
            'unit': detail.unit,
            'quantity': detail.quantity,
            'unit_price': detail.unit_price,
            'amount': detail.amount
        })
    
    return jsonify(result), 200

@app.route('/api/budgets', methods=['GET'])
def get_budgets():
    if 'user_id' not in session:
        return jsonify({'message': '请先登录'}), 401

    # 支持状态过滤
    status_filter = request.args.get('status')
    if status_filter:
        budgets = Budget.query.filter_by(status=status_filter).all()
    else:
        budgets = Budget.query.all()

    result = []
    for budget in budgets:
        result.append({
            'id': budget.id,
            'project_name': budget.project.name,
            'creator_name': budget.creator.username,
            'created_at': budget.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': budget.status,
            'total_amount': budget.total_amount,
            'approver_name': 'admin',  # 示例数据
            'approved_at': budget.create_time.strftime('%Y-%m-%d %H:%M:%S') if budget.status == '已审批' else None
        })
    return jsonify(result), 200

@app.route('/api/budgets/<int:budget_id>/status', methods=['PUT'])
def update_budget_status(budget_id):
    if 'user_id' not in session or session['role'] not in ['领导', '项目经理']:
        return jsonify({'message': '权限不足'}), 403
    
    data = request.json
    new_status = data.get('status')
    
    if new_status not in ['待审批', '已审批', '已驳回']:
        return jsonify({'message': '无效的状态值'}), 400
    
    budget = Budget.query.get_or_404(budget_id)
    budget.status = new_status
    db.session.commit()
    
    return jsonify({'message': '预算状态已更新', 'status': new_status}), 200

# 初始化数据库
def create_tables():
    with app.app_context():
        db.create_all()

        # 添加测试数据 - 强制重新初始化
        # 清空现有数据
        db.session.query(BudgetDetail).delete()
        db.session.query(Budget).delete()
        db.session.query(Project).delete()
        db.session.query(User).delete()
        db.session.commit()

        # 重新创建测试数据
        # 创建管理员用户
        admin = User(username='admin', role='领导')
        admin.set_password('admin123')
        db.session.add(admin)

        # 创建预算员用户
        budgeter = User(username='budgeter', role='预算员')
        budgeter.set_password('budgeter123')
        db.session.add(budgeter)

        # 创建项目经理
        manager = User(username='manager', role='项目经理')
        manager.set_password('manager123')
        db.session.add(manager)

        # 创建项目
        project1 = Project(
            name='跨江大桥建设项目',
            start_date=datetime.datetime(2025, 6, 1),
            manager=manager
        )
        db.session.add(project1)

        project2 = Project(
            name='高层写字楼建设项目',
            start_date=datetime.datetime(2025, 7, 1),
            manager=manager
        )
        db.session.add(project2)

        project3 = Project(
            name='高速公路扩建项目',
            start_date=datetime.datetime(2025, 8, 1),
            manager=manager
        )
        db.session.add(project3)

        project4 = Project(
            name='水利枢纽工程',
            start_date=datetime.datetime(2025, 9, 1),
            manager=manager
        )
        db.session.add(project4)

        project5 = Project(
            name='城市地铁建设项目',
            start_date=datetime.datetime(2025, 10, 1),
            manager=manager
        )
        db.session.add(project5)

        project6 = Project(
            name='现代工业园区建设',
            start_date=datetime.datetime(2025, 11, 1),
            manager=manager
        )
        db.session.add(project6)

        db.session.commit()

        # 创建示例预算 - 高层写字楼建设项目
        sample_budget = Budget(
            project_id=2,  # 高层写字楼建设项目
            creator_id=2,  # budgeter用户
            status='已审批',
            total_amount=2850000.00
        )
        db.session.add(sample_budget)
        db.session.commit()

        # 添加示例预算明细 - 高层写字楼建设项目
        sample_details = [
                # 材料费用 (8项)
                {'item_type': '材料', 'item_name': '高强度水泥', 'specification': '普通硅酸盐水泥 52.5级', 'unit': '吨', 'quantity': 350, 'unit_price': 520},
                {'item_type': '材料', 'item_name': '高强钢筋', 'specification': 'HRB500E φ16-32mm', 'unit': '吨', 'quantity': 120, 'unit_price': 5800},
                {'item_type': '材料', 'item_name': '高标号混凝土', 'specification': 'C40商品混凝土', 'unit': '立方米', 'quantity': 500, 'unit_price': 580},
                {'item_type': '材料', 'item_name': '加气混凝土砌块', 'specification': 'B06级 600×200×100mm', 'unit': '立方米', 'quantity': 200, 'unit_price': 280},
                {'item_type': '材料', 'item_name': '钢化玻璃幕墙', 'specification': '12mm+12A+6mm中空玻璃', 'unit': '平方米', 'quantity': 800, 'unit_price': 450},
                {'item_type': '材料', 'item_name': '铝合金型材', 'specification': '6063-T5断桥铝型材', 'unit': '吨', 'quantity': 15, 'unit_price': 18000},
                {'item_type': '材料', 'item_name': '防水材料', 'specification': 'SBS改性沥青防水卷材', 'unit': '平方米', 'quantity': 1200, 'unit_price': 35},
                {'item_type': '材料', 'item_name': '保温材料', 'specification': 'XPS挤塑聚苯板 50mm', 'unit': '平方米', 'quantity': 1500, 'unit_price': 28},

                # 人工费用 (5项)
                {'item_type': '人工', 'item_name': '高级建筑工程师', 'specification': '一级建造师', 'unit': '人月', 'quantity': 8, 'unit_price': 15000},
                {'item_type': '人工', 'item_name': '结构工程师', 'specification': '高级工程师', 'unit': '人月', 'quantity': 6, 'unit_price': 13000},
                {'item_type': '人工', 'item_name': '技术工人', 'specification': '高级技工', 'unit': '人月', 'quantity': 25, 'unit_price': 9000},
                {'item_type': '人工', 'item_name': '普通建筑工人', 'specification': '中级技工', 'unit': '人月', 'quantity': 40, 'unit_price': 6500},
                {'item_type': '人工', 'item_name': '辅助工人', 'specification': '普通劳务', 'unit': '人月', 'quantity': 20, 'unit_price': 4500},

                # 设备租赁 (3项)
                {'item_type': '设备', 'item_name': '大型塔吊', 'specification': 'QTZ125塔式起重机', 'unit': '台月', 'quantity': 4, 'unit_price': 22000},
                {'item_type': '设备', 'item_name': '高压混凝土泵车', 'specification': '52米泵车', 'unit': '台月', 'quantity': 3, 'unit_price': 25000},
                {'item_type': '设备', 'item_name': '施工升降机', 'specification': 'SC200/200双笼升降机', 'unit': '台月', 'quantity': 2, 'unit_price': 18000},

                # 其他费用 (2项)
                {'item_type': '其他', 'item_name': '高空安全防护', 'specification': '安全网、防护栏、安全带等', 'unit': '项', 'quantity': 1, 'unit_price': 45000},
                {'item_type': '其他', 'item_name': '临时设施建设', 'specification': '办公区、生活区、仓储区', 'unit': '项', 'quantity': 1, 'unit_price': 65000}
        ]

        for detail_data in sample_details:
            quantity = detail_data['quantity']
            unit_price = detail_data['unit_price']
            amount = quantity * unit_price

            detail = BudgetDetail(
                budget_id=sample_budget.id,
                item_type=detail_data['item_type'],
                item_name=detail_data['item_name'],
                specification=detail_data['specification'],
                unit=detail_data['unit'],
                quantity=quantity,
                unit_price=unit_price,
                amount=amount
            )
            db.session.add(detail)

        db.session.commit()

if __name__ == '__main__':
    create_tables()  # 在启动时初始化数据库
    print("启动工程预算管理系统...")
    print("API路由:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
    app.run(debug=False, host='0.0.0.0', port=5001)

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    if 'user_id' not in session:
        return jsonify({'message': '请先登录'}), 401
    
    # 本月预算总额
    today = datetime.date.today()
    month_start = datetime.date(today.year, today.month, 1)
    month_end = datetime.date(today.year, today.month + 1, 1) if today.month < 12 else datetime.date(today.year + 1, 1, 1)
    
    monthly_budgets = Budget.query.filter(
        Budget.create_time >= month_start,
        Budget.create_time < month_end
    ).all()
    
    monthly_total = sum(b.total_amount for b in monthly_budgets)
    
    # 已审批预算总额
    approved_total = sum(b.total_amount for b in Budget.query.filter_by(status='已审批').all())
    
    return jsonify({
        'monthly_total': monthly_total,
        'approved_total': approved_total
    }), 200

# 初始化Flask-Admin
admin = Admin(app, name='工程预算管理系统', template_mode='bootstrap3')

# 自定义模型视图，控制访问权限
class AdminModelView(ModelView):
    def is_accessible(self):
        return 'user_id' in session and session['role'] in ['领导', '项目经理']

# 添加模型视图到管理界面
admin.add_view(AdminModelView(User, db.session, name='用户管理'))
admin.add_view(AdminModelView(Project, db.session, name='项目管理'))
admin.add_view(AdminModelView(Budget, db.session, name='预算管理'))
admin.add_view(AdminModelView(BudgetDetail, db.session, name='预算明细'))
#!/usr/bin/env python3
import eventlet
eventlet.monkey_patch()

import sys
import os
import json
import time
import platform
import subprocess
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

//- ######################################
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app, async_mode='eventlet')

# === 配置文件管理 ===
CONFIG_FILE = 'robot_configs.json'

def load_configs():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_configs(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# === 全局状态 ===
STATE = {
    'connected_ip': None,
    'chassis_on': False,
    'mode': 'REMOTE',
    'speed': 0.0,
    'gear': 'N'
}

def ping_host(ip):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    wait = '-w' if platform.system().lower() == 'windows' else '-W'
    command = ['ping', param, '1', wait, '1', ip]
    try:
        # 模拟真实 Ping
        return (subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0)
    except:
        return False

@app.route('/')
def index():
    return render_template('index.html')

# --- 1. 初始化：前端加载时请求配置列表 ---
@socketio.on('get_configs')
def handle_get_configs():
    configs = load_configs()
    emit('config_list', configs)

# --- 2. 保存配置 ---
@socketio.on('save_config')
def handle_save_config(data):
    name = data.get('name')
    ip = data.get('ip')
    if not name or not ip: return
    
    configs = load_configs()
    configs[name] = ip
    save_configs(configs)
    
    emit('log', {'msg': f"配置 '{name}' 已保存", 'type': 'success'})
    emit('config_list', configs) # 刷新前端列表

# --- 3. 删除配置 ---
@socketio.on('delete_config')
def handle_delete_config(data):
    name = data.get('name')
    configs = load_configs()
    if name in configs:
        del configs[name]
        save_configs(configs)
        emit('log', {'msg': f"配置 '{name}' 已删除", 'type': 'warning'})
        emit('config_list', configs)

# --- 4. 连接设备 ---
@socketio.on('connect_device')
def handle_connect(data):
    target_ip = data.get('ip')
    if ping_host(target_ip):
        STATE['connected_ip'] = target_ip
        emit('log', {'msg': f"连接成功: {target_ip}", 'type': 'success'})
        emit('conn_status', {'connected': True, 'ip': target_ip})
    else:
        STATE['connected_ip'] = None
        emit('log', {'msg': f"连接失败: {target_ip}", 'type': 'error'})
        emit('conn_status', {'connected': False})

# ... (其余控制逻辑保持不变，为了节省篇幅这里简化) ...
@socketio.on('toggle_chassis')
def handle_chassis():
    # 简单的模拟逻辑
    STATE['chassis_on'] = not STATE['chassis_on']
    msg = "底盘已启动" if STATE['chassis_on'] else "底盘已停止"
    type_ = "success" if STATE['chassis_on'] else "warning"
    emit('log', {'msg': msg, 'type': type_})
    emit('state_sync', STATE)

@socketio.on('cmd_sim')
def handle_cmd(data):
    if not STATE['chassis_on']: return
    key = data.get('key')
    v = 0.3 if key in ['I','U','O'] else (-0.3 if key in [',','M','.'] else 0.0)
    STATE['gear'] = 'D' if v > 0 else ('R' if v < 0 else 'N')
    emit('hud_update', {'v': v, 'gear': STATE['gear']})

if __name__ == '__main__':
    print("启动成功: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000)

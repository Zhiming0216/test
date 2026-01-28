
const socket = io();
let is_connected = false;
let saved_configs = {}; // 本地缓存配置

// 初始化：请求配置列表
socket.emit('get_configs');

// === 1. 配置管理逻辑 ===

// 接收后端发来的配置列表
socket.on('config_list', (data) => {
    saved_configs = data;
    const select = document.getElementById('saved-robots');
    
    // 清空除了第一项以外的选项
    select.innerHTML = '<option value="" selected>-- 新建/手动输入 --</option>';
    
    // 填充下拉框
    for (const [name, ip] of Object.entries(data)) {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = `${name} (${ip})`;
        select.appendChild(option);
    }
});

// 下拉框改变时触发
function loadSelectedConfig() {
    const name = document.getElementById('saved-robots').value;
    const inputName = document.getElementById('input-name');
    const inputIp = document.getElementById('input-ip');

    if (name && saved_configs[name]) {
        // 如果选中了已有的，自动填入
        inputName.value = name;
        inputIp.value = saved_configs[name];
    } else {
        // 如果选了新建，清空
        inputName.value = "";
        inputIp.value = "192.168.";
    }
}

// 保存配置
function saveConfig() {
    const name = document.getElementById('input-name').value.trim();
    const ip = document.getElementById('input-ip').value.trim();
    
    if(!name || !ip) {
        alert("名称和IP不能为空");
        return;
    }
    socket.emit('save_config', {name: name, ip: ip});
}

// 删除配置
function deleteConfig() {
    const name = document.getElementById('input-name').value.trim();
    if(!name || !saved_configs[name]) {
        alert("请先选择一个有效的配置");
        return;
    }
    if(confirm(`确定要删除 ${name} 吗？`)) {
        socket.emit('delete_config', {name: name});
        // 清空输入框
        document.getElementById('saved-robots').value = "";
        loadSelectedConfig();
    }
}

// === 2. 页面与连接逻辑 ===

function showPage(pageId) {
    if (pageId !== 'connect' && !is_connected) { alert("请先连接设备！"); return; }
    document.querySelectorAll('.content-section').forEach(el => el.classList.add('d-none'));
    document.getElementById('page-' + pageId).classList.remove('d-none');
    document.querySelectorAll('.list-group-item').forEach(el => el.classList.remove('active'));
    document.getElementById('nav-' + pageId).classList.add('active');
}

function connectDevice() {
    const ip = document.getElementById('input-ip').value;
    document.getElementById('conn-msg').textContent = "正在连接...";
    socket.emit('connect_device', {ip: ip});
}

socket.on('conn_status', (data) => {
    is_connected = data.connected;
    const statusText = document.getElementById('status-text');
    const msg = document.getElementById('conn-msg');
    const btn = document.getElementById('nav-basic');

    if (is_connected) {
        statusText.innerText = "已连接";
        statusText.classList.add('text-success');
        msg.textContent = "连接成功!";
        msg.className = "text-success fw-bold align-self-center small";
        btn.classList.remove('disabled');
        // 自动跳转
        setTimeout(() => showPage('basic'), 500);
    } else {
        statusText.innerText = "未连接";
        statusText.classList.remove('text-success');
        msg.textContent = "连接失败，请检查IP";
        msg.className = "text-danger fw-bold align-self-center small";
        btn.classList.add('disabled');
    }
});

// === 3. 其他控制逻辑 (简化版) ===
function toggleChassis() { socket.emit('toggle_chassis'); }
socket.on('log', (data) => {
    const box = document.getElementById('log-box');
    box.value += `> ${data.msg}\n`;
});
socket.on('hud_update', (data) => {
    document.getElementById('hud-gear').textContent = data.gear;
});
document.addEventListener('keydown', (e) => {
    const map = {'i':'I', ',':',', 'k':'K'};
    if(map[e.key.toLowerCase()]) socket.emit('cmd_sim', {key: map[e.key.toLowerCase()]});
});

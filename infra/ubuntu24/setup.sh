#!/usr/bin/env bash
set -euo pipefail

# ---- 1. 切换为清华源（Ubuntu 24.04 用新格式 ubuntu.sources）----
SRC=/etc/apt/sources.list.d/ubuntu.sources
if [ -f "$SRC" ]; then
  # 先用 http 让 apt 能在没有 ca-certificates 的情况下握手
  sed -i 's|http://archive.ubuntu.com|http://mirrors.tuna.tsinghua.edu.cn|g; s|http://security.ubuntu.com|http://mirrors.tuna.tsinghua.edu.cn|g; s|https://mirrors.tuna.tsinghua.edu.cn|http://mirrors.tuna.tsinghua.edu.cn|g' "$SRC"
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
# 第一波：先装 CA 证书
apt-get install -y --no-install-recommends ca-certificates
# 装好之后切回 https
if [ -f "$SRC" ]; then
  sed -i 's|http://mirrors.tuna.tsinghua.edu.cn|https://mirrors.tuna.tsinghua.edu.cn|g' "$SRC"
fi
apt-get update -y
apt-get install -y --no-install-recommends \
  curl wget git vim sudo openssh-server \
  net-tools iputils-ping iproute2 dnsutils \
  htop tmux less unzip zip tzdata locales build-essential

# ---- 2. 时区 + 中文 locale ----
ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
echo "Asia/Shanghai" > /etc/timezone
locale-gen zh_CN.UTF-8 en_US.UTF-8 || true

# ---- 3. 创建 dev 用户（sudo 免密）----
DEV_USER="${DEV_USER:-dev}"
DEV_PASS="${DEV_PASS:-dev123456}"
if ! id -u "$DEV_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$DEV_USER"
fi
echo "$DEV_USER:$DEV_PASS" | chpasswd
usermod -aG sudo "$DEV_USER"
echo "$DEV_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-$DEV_USER
chmod 440 /etc/sudoers.d/90-$DEV_USER

# root 也设个密码（仅用于 docker exec 救急）
echo "root:${ROOT_PASS:-root123456}" | chpasswd

# ---- 4. SSH 配置 ----
mkdir -p /var/run/sshd /etc/ssh
ssh-keygen -A   # 自动生成主机密钥（如缺）
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#\?UsePAM.*/UsePAM yes/' /etc/ssh/sshd_config

# 让 sshd 开机自启：写入一个 init 脚本由 docker 主进程调用
cat >/usr/local/bin/container-init.sh <<'EOF'
#!/usr/bin/env bash
mkdir -p /var/run/sshd
/usr/sbin/sshd -D -e
EOF
chmod +x /usr/local/bin/container-init.sh

echo "[done] user=$DEV_USER  pass=$DEV_PASS  ssh_port_host=2222"

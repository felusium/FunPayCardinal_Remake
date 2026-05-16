#!/usr/bin/env bash
set -Eeuo pipefail

REPO_OWNER="felusium"
REPO_NAME="FunPayCardinal_Remake"
BRANCH="main"
APP_DIR_NAME="FunPayCardinal_Remake"
SERVICE_NAME="FunPayCardinal"
PYTHON_BIN="python3"

RED="\033[1;91m"
GREEN="\033[1;92m"
CYAN="\033[1;96m"
RESET="\033[0m"

fail() {
  echo -e "${RED}Ошибка:${RESET} $1" >&2
  exit 1
}

run() {
  echo -e "${CYAN}$*${RESET}"
  "$@"
}

if ! command -v sudo >/dev/null 2>&1; then
  fail "sudo не найден. Запустите скрипт на Ubuntu/Debian с установленным sudo."
fi

echo -e "${GREEN}Установка ${APP_DIR_NAME}${RESET}"
echo -ne "${CYAN}Введите пользователя Linux для запуска бота [fpc]: ${RESET}"
read -r APP_USER
APP_USER="${APP_USER:-fpc}"

if [[ ! "$APP_USER" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
  fail "Некорректное имя пользователя: $APP_USER"
fi

if ! id "$APP_USER" >/dev/null 2>&1; then
  run sudo useradd -m -s /bin/bash "$APP_USER"
fi

APP_HOME="$(eval echo "~$APP_USER")"
APP_DIR="$APP_HOME/$APP_DIR_NAME"
VENV_DIR="$APP_HOME/pyvenv"
TMP_DIR="$(mktemp -d)"
ARCHIVE_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${BRANCH}.zip"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo -e "${GREEN}Устанавливаю системные пакеты...${RESET}"
run sudo apt update
run sudo apt install -y python3 python3-venv python3-pip unzip curl ca-certificates

echo -e "${GREEN}Скачиваю исходники из твоего репозитория...${RESET}"
run curl -L "$ARCHIVE_URL" -o "$TMP_DIR/source.zip"
run unzip -q "$TMP_DIR/source.zip" -d "$TMP_DIR"

SRC_DIR="$(find "$TMP_DIR" -maxdepth 1 -type d -name "${REPO_NAME}-*" | head -n 1)"
if [[ -z "${SRC_DIR:-}" || ! -d "$SRC_DIR" ]]; then
  fail "Не удалось найти распакованную папку проекта."
fi

echo -e "${GREEN}Копирую файлы в ${APP_DIR}...${RESET}"
run sudo rm -rf "$APP_DIR"
run sudo mkdir -p "$APP_DIR"
run sudo cp -a "$SRC_DIR/." "$APP_DIR/"
run sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo -e "${GREEN}Создаю виртуальное окружение...${RESET}"
run sudo -u "$APP_USER" "$PYTHON_BIN" -m venv "$VENV_DIR"
run sudo -u "$APP_USER" "$VENV_DIR/bin/python" -m pip install -U pip
run sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

echo -e "${GREEN}Создаю systemd-сервис...${RESET}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}@.service"
sudo tee "$SERVICE_FILE" >/dev/null <<EOF
[Unit]
Description=${APP_DIR_NAME} Bot Service (%i)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=%i
WorkingDirectory=/home/%i/${APP_DIR_NAME}
Environment=FPC_IS_RUNNIG_AS_SERVICE=1
ExecStart=/home/%i/pyvenv/bin/python /home/%i/${APP_DIR_NAME}/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

run sudo systemctl daemon-reload

CONFIG_FILE="$APP_DIR/configs/_main.cfg"
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo -e "${GREEN}Запускаю первичную настройку. Ответьте на вопросы в консоли.${RESET}"
  sudo -u "$APP_USER" "$VENV_DIR/bin/python" "$APP_DIR/main.py"
fi

echo -e "${GREEN}Запускаю сервис...${RESET}"
run sudo systemctl restart "${SERVICE_NAME}@${APP_USER}.service"

echo -e "${GREEN}Готово.${RESET}"
echo -e "Статус: ${CYAN}sudo systemctl status ${SERVICE_NAME}@${APP_USER}.service -n 100${RESET}"
echo -e "Остановить: ${CYAN}sudo systemctl stop ${SERVICE_NAME}@${APP_USER}.service${RESET}"
echo -e "Запустить: ${CYAN}sudo systemctl start ${SERVICE_NAME}@${APP_USER}.service${RESET}"
echo -e "Автозагрузка: ${CYAN}sudo systemctl enable ${SERVICE_NAME}@${APP_USER}.service${RESET}"

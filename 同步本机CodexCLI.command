#!/bin/bash
cd "$(dirname "$0")"

LOG_DIR="$PWD/logs"
mkdir -p "$LOG_DIR"
LOG_PATH="$LOG_DIR/codex-cli-sync-$(date +%Y%m%d-%H%M%S).log"

check_codex_login() {
    local output status
    output="$("$CODEX_BIN" login status 2>&1)"
    status=$?
    if [ "$status" -eq 0 ] && ! printf '%s' "$output" | grep -Eiq 'not logged|login required|unauthorized|not authenticated'; then
        return 0
    fi
    if [ -f "$HOME/.codex/auth.json" ] && grep -Eq '"(OPENAI_API_KEY|access_token|refresh_token)"' "$HOME/.codex/auth.json"; then
        return 0
    fi
    return 1
}

{
    echo "=== Codex CLI 本机登录态同步 ==="
    echo "工作目录: $PWD"
    echo ""

    CODEX_BIN="$(command -v codex || true)"
    if [ -z "$CODEX_BIN" ]; then
        echo "未找到 codex 命令。请先安装 Codex CLI，并确认终端 PATH 可访问 codex。"
        echo ""
        echo "日志: $LOG_PATH"
        echo "按 Enter 键关闭..."
        read -r
        exit 1
    fi

    echo "找到 codex: $CODEX_BIN"
    "$CODEX_BIN" --version || true
    echo ""

    if ! "$CODEX_BIN" exec --help >/dev/null 2>&1; then
        echo "当前 Codex CLI 不支持 codex exec，请先升级 Codex CLI。"
        echo ""
        echo "日志: $LOG_PATH"
        echo "按 Enter 键关闭..."
        read -r
        exit 1
    fi

    if ! check_codex_login; then
        echo "未检测到 Codex 登录态，开始执行 codex login..."
        "$CODEX_BIN" login
        echo ""
    fi

    if ! check_codex_login; then
        echo "仍未检测到可用登录态。请确认 codex login 已完成后重新运行本脚本。"
        echo ""
        echo "日志: $LOG_PATH"
        echo "按 Enter 键关闭..."
        read -r
        exit 1
    fi

    API_DIR="$PWD/API"
    ENV_PATH="$API_DIR/.env"
    mkdir -p "$API_DIR"
    touch "$ENV_PATH"
    TMP_PATH="$ENV_PATH.tmp.$$"
    CODEX_AUTH_DIR="$HOME/.codex"
    CODEX_AUTH_FILE="$CODEX_AUTH_DIR/auth.json"
    grep -vE '^(CODEX_CLI_USE_LOCAL_AUTH|CODEX_CLI_AUTH_CONFIGURED|CODEX_CLI_BIN|CODEX_CLI_AUTH_FILE|CODEX_CLI_HOME)=' "$ENV_PATH" > "$TMP_PATH" || true
    printf 'CODEX_CLI_USE_LOCAL_AUTH=1\n' >> "$TMP_PATH"
    printf 'CODEX_CLI_AUTH_CONFIGURED=1\n' >> "$TMP_PATH"
    printf 'CODEX_CLI_BIN=%s\n' "$CODEX_BIN" >> "$TMP_PATH"
    printf 'CODEX_CLI_AUTH_FILE=%s\n' "$CODEX_AUTH_FILE" >> "$TMP_PATH"
    printf 'CODEX_CLI_HOME=%s\n' "$CODEX_AUTH_DIR" >> "$TMP_PATH"
    mv "$TMP_PATH" "$ENV_PATH"

    echo "已更新 API/.env:"
    echo "  CODEX_CLI_USE_LOCAL_AUTH=1"
    echo "  CODEX_CLI_AUTH_CONFIGURED=1"
    echo "  CODEX_CLI_BIN=$CODEX_BIN"
    echo "  CODEX_CLI_AUTH_FILE=$CODEX_AUTH_FILE"
    echo "  CODEX_CLI_HOME=$CODEX_AUTH_DIR"
    echo ""
    echo "测试连通性..."
    "$CODEX_BIN" login status || true
    echo ""
    echo "完成。刷新 API 设置页面后，Codex CLI 应显示为已配置。"
    echo ""
    echo "日志: $LOG_PATH"
    echo "按 Enter 键关闭..."
    read -r
} 2>&1 | tee -a "$LOG_PATH"

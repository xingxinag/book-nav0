#!/bin/sh
# 备份清理脚本 - 保留最近30个备份，删除更早的备份

BACKUP_DIR="/app/app/backups"
MAX_BACKUPS=30

# 计算要删除的文件数量
file_count=$(ls -1 $BACKUP_DIR/*.db3 2>/dev/null | wc -l)
delete_count=$((file_count - MAX_BACKUPS))

if [ $delete_count -gt 0 ]; then
    echo "发现 $file_count 个备份文件，保留最新的 $MAX_BACKUPS 个，删除 $delete_count 个..."
    ls -1t $BACKUP_DIR/*.db3 | tail -n $delete_count | xargs rm -f
    echo "备份清理完成"
else
    echo "当前备份数量($file_count)未超过上限($MAX_BACKUPS)，无需清理"
fi 
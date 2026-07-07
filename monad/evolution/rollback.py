"""
RollbackManager — every apply is preceded by a backup, so every change is reversible.

Backups are kept in memory_data/evolution_backups/<record_id>/ so they live on
the USB and survive across sessions.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from monad.core.logger import get_logger

log = get_logger(__name__)


class RollbackManager:
    def __init__(self, root: Path, backups_dir: Path) -> None:
        self.root = Path(root)
        self.backups_dir = Path(backups_dir)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, target_path: str, record_id: str) -> str:
        """Save a copy of the current file (if it exists). Returns backup path."""
        src = self.root / target_path
        backup_dir = self.backups_dir / record_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / Path(target_path).name

        if src.exists():
            shutil.copy2(src, backup_file)
            log.debug("Backed up {} -> {}", src, backup_file)
        else:
            # Placeholder marker for a "file did not exist before"
            (backup_dir / ".was_new").write_text(target_path, encoding="utf-8")

        return str(backup_file)

    def rollback(self, record) -> bool:
        """Given an EvolutionRecord, restore the pre-change state."""
        target = self.root / record.target_path
        backup_dir = self.backups_dir / record.id

        if (backup_dir / ".was_new").exists():
            # File didn't exist before — delete the new one
            if target.exists():
                target.unlink()
                log.info("Rollback: deleted newly-created {}", target)
            return True

        backup_file = backup_dir / Path(record.target_path).name
        if not backup_file.exists():
            log.error("Cannot rollback {}: no backup at {}", record.id, backup_file)
            return False

        shutil.copy2(backup_file, target)
        log.info("Rollback: restored {} from {}", target, backup_file)
        return True

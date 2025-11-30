import sys
import json


class _Notify:
    """Notification emitter (writes to stderr)."""

    def _emit(self, data: dict) -> None:
        print(json.dumps(data), file=sys.stderr, flush=True)

    def progress(self, message: str, percent: int | None = None) -> None:
        event = {
            "type": "notification",
            "kind": "progress",
            "message": message,
        }
        if percent is not None:
            event["percent"] = percent
        self._emit(event)

    def log(self, message: str, level: str = "info") -> None:
        self._emit({
            "type": "notification",
            "kind": "log",
            "level": level,
            "message": message,
        })

    def artifact(self, name: str, uri: str) -> None:
        self._emit({
            "type": "notification",
            "kind": "artifact",
            "name": name,
            "uri": uri,
        })


# Singleton instance
notify = _Notify()

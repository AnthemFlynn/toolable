from typing import Any


class Response:
    @staticmethod
    def success(result: dict[str, Any]) -> dict:
        return {"status": "success", "result": result}

    @staticmethod
    def error(
        code: str,
        message: str,
        recoverable: bool = False,
        suggestion: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict:
        error_obj = {
            "code": code,
            "message": message,
            "recoverable": recoverable,
        }
        if suggestion:
            error_obj["suggestion"] = suggestion
        if context:
            error_obj["context"] = context

        return {"status": "error", "error": error_obj}

    @staticmethod
    def partial(
        result: dict[str, Any],
        errors: list[dict],
        result_key: str | None = None,
    ) -> dict:
        # Auto-detect result key if not specified
        succeeded_count = 0
        if result_key:
            succeeded_count = len(result.get(result_key, []))
        else:
            for v in result.values():
                if isinstance(v, list):
                    succeeded_count = len(v)
                    break

        failed_count = len(errors)
        recoverable_count = sum(1 for e in errors if e.get("recoverable", False))

        # Determine status
        if failed_count == 0:
            status = "success"
        elif succeeded_count == 0:
            status = "error"
        else:
            status = "partial"

        response = {
            "status": status,
            "result": result,
            "summary": {
                "total": succeeded_count + failed_count,
                "succeeded": succeeded_count,
                "failed": failed_count,
                "recoverable_failures": recoverable_count,
            },
        }

        if errors:
            response["errors"] = errors

        return response

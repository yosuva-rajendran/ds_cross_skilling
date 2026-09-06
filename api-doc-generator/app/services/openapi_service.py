import json

import yaml


class OpenAPIService:

    @staticmethod
    def load_file(
        filename: str,
        content: bytes,
    ) -> dict:

        if filename.endswith(".json"):
            return json.loads(
                content.decode("utf-8")
            )

        if filename.endswith((".yaml", ".yml")):
            return yaml.safe_load(
                content.decode("utf-8")
            )

        raise ValueError(
            "Unsupported file format. Use JSON or YAML."
        )
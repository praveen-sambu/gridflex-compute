from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.voice_agent import export_voice_agent_artifacts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Export GridFlex voice-agent session logs and generated audio artifacts.")
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "artifacts" / "voice-agent-session-export"),
        help="Destination directory for the exported voice-agent artifacts.",
    )
    args = parser.parse_args()

    result = export_voice_agent_artifacts(Path(args.output_dir))
    print(f"destination={result['destination']}")
    for file_name in result["files"]:
      print(f"file={file_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
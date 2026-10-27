
from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path(__file__).resolve().parent

BACKEND = ROOT / "backend" / "app" / "runs.py"
FRONTEND = ROOT / "frontend" / "app" / "runs" / "[id]" / "page.tsx"
API = ROOT / "frontend" / "lib" / "api.ts"

for path in (BACKEND, FRONTEND, API):
    if not path.is_file():
        sys.exit(f"File not found: {path}")

backend = BACKEND.read_text(encoding="utf-8-sig")
frontend = FRONTEND.read_text(encoding="utf-8-sig")
api = API.read_text(encoding="utf-8-sig")


def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: expected 1 match, found {count}. "
            "No files have been modified."
        )
    return source.replace(old, new, 1)


if "def get_run_evidence(" in backend:
    sys.exit(
        "Secure evidence endpoint already exists. "
        "No changes made."
    )

if "function useEvidenceObjectUrl(" in frontend:
    sys.exit(
        "Frontend evidence support already exists. "
        "No changes made."
    )

# ============================================================
# BACKEND: AUTHENTICATED SCREENSHOT ENDPOINT
# ============================================================

backend = replace_once(
    backend,
    "from fastapi import APIRouter, Depends, HTTPException",
    "from fastapi import APIRouter, Depends, HTTPException\n"
    "from fastapi.responses import FileResponse",
    "Backend imports",
)

route_marker = (
    "\n# ============================================================\n"
    "# DELETE AUTHORIZED RUN\n"
    "# ============================================================\n"
)

secure_route = '''
# ============================================================
# SECURE SCREENSHOT EVIDENCE
# ============================================================

@router.get("/{run_id}/evidence/{filename}")
def get_run_evidence(
    run_id: str,
    filename: str,
    current_user: dict = Depends(get_current_user),
):
    run = require_owned_run(run_id, current_user)

    if (
        not filename
        or filename in {".", ".."}
        or Path(filename).name != filename
        or "\\\\" in filename
        or not filename.lower().endswith(".png")
    ):
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    def stored_filename(value):
        if not isinstance(value, str) or not value:
            return None
        return Path(value.replace("\\\\", "/")).name

    allowed = set()

    def add(value):
        name = stored_filename(value)
        if name:
            allowed.add(name)

    add(run.get("screenshot"))

    for step in run.get("steps") or []:
        if isinstance(step, dict):
            for key in (
                "screenshot",
                "screenshot_path",
                "evidence_path",
            ):
                add(step.get(key))

    for verification in run.get("verifications") or []:
        if isinstance(verification, dict):
            for key in (
                "screenshot",
                "screenshot_path",
                "evidence_path",
            ):
                add(verification.get(key))

    for item in run.get("evidence") or []:
        if isinstance(item, dict):
            for key in (
                "url",
                "screenshot",
                "path",
                "evidence_path",
            ):
                add(item.get(key))

    if filename not in allowed:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    evidence_dir = (
        Path(__file__).resolve().parent.parent / "evidence"
    ).resolve()

    candidate = (evidence_dir / filename).resolve()

    if (
        candidate.parent != evidence_dir
        or not candidate.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    return FileResponse(
        candidate,
        media_type="image/png",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )

'''

backend = replace_once(
    backend,
    route_marker,
    "\n" + secure_route + route_marker,
    "Secure evidence endpoint",
)

backend = replace_once(
    backend,
    '        "evidence": unique_evidence,',
    '        "evidence": unique_evidence,\n'
    '        "screenshot": evidence_url_from_path('
    'run.get("screenshot")),',
    "Final screenshot serialization",
)

# ============================================================
# API: FETCH SCREENSHOTS WITH JWT AUTHENTICATION
# ============================================================

api_helper = r'''

export async function fetchEvidenceBlob(
  runId: string,
  path: string
): Promise<Blob> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("test_ai_token")
      : null;

  if (!token) {
    throw new Error("Please sign in to view evidence.");
  }

  const filename = path
    .replace(/\\/g, "/")
    .split("/")
    .pop();

  if (
    !filename ||
    !/^[a-zA-Z0-9_-]+\.png$/i.test(filename)
  ) {
    throw new Error("Invalid screenshot filename.");
  }

  const response = await fetch(
    `${API}/api/runs/${encodeURIComponent(runId)}/evidence/${encodeURIComponent(filename)}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      `Evidence unavailable (${response.status})`
    );
  }

  return await response.blob();
}
'''

if "fetchEvidenceBlob(" in api:
    raise RuntimeError(
        "API evidence helper already exists."
    )

api = api.rstrip() + "\n" + api_helper

# ============================================================
# FRONTEND: AUTHENTICATED IMAGE LOADING
# ============================================================

frontend = replace_once(
    frontend,
    'import { api } from "@/lib/api";',
    'import { api, fetchEvidenceBlob } from "@/lib/api";',
    "Frontend API import",
)

start = frontend.index(
    "function evidenceUrl(path?: string) {"
)
end = frontend.index(
    "\nfunction StatusBadge(",
    start,
)

image_helper = '''
function useEvidenceObjectUrl(
  path?: string,
  runId?: string
) {
  const [url, setUrl] = useState("");

  useEffect(() => {
    if (!path || !runId) {
      setUrl("");
      return;
    }

    let cancelled = false;
    let objectUrl = "";

    setUrl("");

    fetchEvidenceBlob(runId, path)
      .then((blob) => {
        if (cancelled) return;

        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch((error) => {
        if (!cancelled) {
          console.warn(
            "Screenshot unavailable:",
            error
          );
        }
      });

    return () => {
      cancelled = true;

      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [path, runId]);

  return url;
}

function EvidenceTile({
  item,
  runId,
}: {
  item: Evidence;
  runId: string;
}) {
  const url = useEvidenceObjectUrl(
    item.url,
    runId
  );

  return (
    <a
      href={url || undefined}
      target="_blank"
      rel="noopener noreferrer"
      style={styles.evidenceCard}
    >
      {url ? (
        <img
          src={url}
          alt={item.name || "Execution evidence"}
          style={styles.evidenceImage}
        />
      ) : (
        <div
          style={{
            ...styles.evidenceImage,
            padding: 16,
            color: COLORS.muted,
          }}
        >
          Loading evidence or screenshot unavailable
        </div>
      )}

      <div style={styles.evidenceInfo}>
        <small style={{ color: COLORS.purple }}>
          {formatAction(item.type)}
        </small>

        <strong>
          {item.name || "Test Evidence"}
        </strong>
      </div>
    </a>
  );
}
'''

frontend = (
    frontend[:start]
    + image_helper
    + frontend[end:]
)

frontend = replace_once(
    frontend,
    "function Screenshot({\n  path,\n  title,",
    "function Screenshot({\n  path,\n  title,\n  runId,",
    "Screenshot component signature",
)

frontend = replace_once(
    frontend,
    '  title: string;\n}) {\n'
    '  if (!path) return null;\n\n'
    '  const url = evidenceUrl(path);',
    '  title: string;\n'
    '  runId: string;\n'
    '}) {\n'
    '  const url = useEvidenceObjectUrl(path, runId);\n'
    '  if (!path) return null;',
    "Screenshot authenticated loading",
)

frontend = replace_once(
    frontend,
    '        href={url}\n'
    '        target="_blank"',
    '        href={url || undefined}\n'
    '        target="_blank"',
    "Screenshot link",
)

frontend = replace_once(
    frontend,
    '          src={url}\n'
    '          alt={title}',
    '          src={url || undefined}\n'
    '          alt={title}',
    "Screenshot image",
)

frontend = replace_once(
    frontend,
    "function VerificationCard({\n"
    "  verification,\n"
    "  index,",
    "function VerificationCard({\n"
    "  verification,\n"
    "  index,\n"
    "  runId,",
    "Verification component signature",
)

frontend = replace_once(
    frontend,
    "  verification: Verification;\n"
    "  index: number;",
    "  verification: Verification;\n"
    "  index: number;\n"
    "  runId: string;",
    "Verification component props",
)

frontend = replace_once(
    frontend,
    '        path={verification.screenshot}\n'
    '        title={`Verification ${index + 1} evidence`}',
    '        path={verification.screenshot}\n'
    '        title={`Verification ${index + 1} evidence`}\n'
    '        runId={runId}',
    "Verification screenshot",
)

frontend = replace_once(
    frontend,
    '                verification={verification}\n'
    '                index={index}',
    '                verification={verification}\n'
    '                index={index}\n'
    '                runId={runId}',
    "Verification render",
)

frontend = replace_once(
    frontend,
    '                    path={step.screenshot}\n'
    '                    title={`Step ${index + 1} evidence`}',
    '                    path={step.screenshot}\n'
    '                    title={`Step ${index + 1} evidence`}\n'
    '                    runId={runId}',
    "Step screenshot",
)

start = frontend.index(
    "              {screenshotItems.map((item, index) => ("
)

end = frontend.index(
    "\n              ))}",
    start,
) + len("\n              ))}")

frontend = (
    frontend[:start]
    + '''              {screenshotItems.map((item, index) => (
                <EvidenceTile
                  key={index}
                  item={item}
                  runId={runId}
                />
              ))}'''
    + frontend[end:]
)

# ============================================================
# VALIDATE BEFORE WRITING
# ============================================================

compile(
    backend,
    str(BACKEND),
    "exec",
)

if "fetchEvidenceBlob" not in frontend:
    raise RuntimeError(
        "Frontend verification failed."
    )

# ============================================================
# BACKUP AND WRITE
# ============================================================

stamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

for path, content in (
    (BACKEND, backend),
    (FRONTEND, frontend),
    (API, api),
):
    backup = path.with_name(
        path.name + ".before_step11a_" + stamp + ".bak"
    )

    shutil.copy2(path, backup)

    path.write_text(
        content,
        encoding="utf-8",
    )

    print("Updated:", path)
    print("Backup:", backup.name)

print()
print("STEP 11A INSTALLED")
print("Next: run backend compile and frontend build.")

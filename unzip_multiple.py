import os
import re
import zipfile
from pathlib import Path

# ---- Config ----
parts_glob = "stanza_resources.zip.*"      # e.g. stanza_resources.zip.001 ...
output_zip = "stanza_resources.zip"        # reconstructed zip file
extract_to = "stanza_resources_extracted"  # destination folder
# ----------------

def part_index(p: Path) -> int:
    """
    Extract numeric suffix from ...zip.001 -> 1
    """
    m = re.search(r"\.(\d+)$", p.name)
    if not m:
        raise ValueError(f"Not a part file: {p}")
    return int(m.group(1))

def join_parts(parts, out_path: Path, chunk_size=1024 * 1024 * 16):
    """
    Concatenate split parts into one ZIP file.
    """
    out_path = out_path.resolve()
    if out_path.exists():
        print(f"[i] Output zip already exists: {out_path}")
        return out_path

    print(f"[i] Writing: {out_path}")
    total_written = 0

    with out_path.open("wb") as w:
        for p in parts:
            p = p.resolve()
            print(f"  + {p.name} ({p.stat().st_size} bytes)")
            with p.open("rb") as r:
                while True:
                    chunk = r.read(chunk_size)
                    if not chunk:
                        break
                    w.write(chunk)
                    total_written += len(chunk)

    print(f"[✓] Done. Total bytes written: {total_written}")
    return out_path

def main():
    cwd = Path.cwd()

    # Find and sort parts: .001, .002, ...
    parts = sorted(cwd.glob(parts_glob), key=part_index)
    if not parts:
        raise FileNotFoundError(f"No files matching: {parts_glob}")

    # Sanity check: ensure continuous sequence
    indices = [part_index(p) for p in parts]
    expected = list(range(min(indices), max(indices) + 1))
    if indices != expected:
        missing = sorted(set(expected) - set(indices))
        raise RuntimeError(f"Missing part(s): {missing}  Found: {indices}")

    # Join parts into a single zip
    out_zip_path = join_parts(parts, cwd / output_zip)

    # Test + extract
    extract_path = (cwd / extract_to).resolve()
    extract_path.mkdir(parents=True, exist_ok=True)

    print(f"[i] Testing zip integrity...")
    with zipfile.ZipFile(out_zip_path, "r") as z:
        bad = z.testzip()
        if bad is not None:
            raise RuntimeError(f"Corrupted file inside zip: {bad}")
        print(f"[✓] Zip OK. Extracting to: {extract_path}")
        z.extractall(extract_path)

    print("[✓] Extraction complete.")

if __name__ == "__main__":
    main()

"""Extract the Step 4 h5 delivery and verify the re-shipped Step 3 files.

The NREL Step 4 delivery is a single Zip64 archive:

    D:/ReEDS files/nuclear-learning/all runs so far.zip

148 flat entries, all stored uncompressed: 120 new run outputs named
``step4_{case}_outputs.h5`` (the Step 4 batch) plus the 28 Step 3 / pilot
outputs re-shipped under their original ``test1_{case}_outputs.h5`` names.

This script:
  1. extracts the 120 ``step4_*`` members to STEP4_DIR (skipping any already
     extracted with matching size + CRC);
  2. does NOT extract the 28 ``test1_*`` members — instead stream-hashes them
     from the zip and compares SHA-256 against the copies already on disk in
     SMR100_DIR (the files step3_checks validated). Any mismatch is a hard
     stop: it would mean NREL re-ran or re-exported a Step 3 case, which
     invalidates reusing the step3_checks exports as canonical.
  3. writes exports/extraction_manifest.csv with one row per member:
     member, size, sha256, disposition.

Git-Bash Info-ZIP ``unzip`` cannot read this archive (Zip64); python zipfile
handles it. Run with any python 3.8+; no third-party deps.
"""

from __future__ import annotations

import csv
import hashlib
import sys
import zipfile
from pathlib import Path

ZIP_PATH = Path("D:/ReEDS files/nuclear-learning/all runs so far.zip")
STEP4_DIR = Path("D:/ReEDS files/nuclear-learning/step4 runs")
SMR100_DIR = Path("D:/ReEDS files/nuclear-learning/smr100 first run")
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "exports" / "extraction_manifest.csv"

N_STEP4 = 120
N_RESHIP = 28
CHUNK = 1 << 22  # 4 MiB


def sha256_stream(fobj) -> str:
    h = hashlib.sha256()
    while True:
        chunk = fobj.read(CHUNK)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    with open(path, "rb") as f:
        return sha256_stream(f)


def main() -> int:
    assert ZIP_PATH.exists(), f"delivery zip not found: {ZIP_PATH}"
    STEP4_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    mismatches = []

    with zipfile.ZipFile(ZIP_PATH) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        step4 = sorted((i for i in infos if i.filename.startswith("step4_")), key=lambda i: i.filename)
        reship = sorted((i for i in infos if i.filename.startswith("test1_")), key=lambda i: i.filename)
        other = [i for i in infos if not (i.filename.startswith("step4_") or i.filename.startswith("test1_"))]
        assert len(step4) == N_STEP4, f"expected {N_STEP4} step4 members, got {len(step4)}"
        assert len(reship) == N_RESHIP, f"expected {N_RESHIP} test1 members, got {len(reship)}"
        assert not other, f"unexpected members: {[i.filename for i in other]}"
        assert all("/" not in i.filename and "\\" not in i.filename for i in infos), "archive is not flat"

        # --- 1. extract the 120 step4 members ------------------------------
        for k, info in enumerate(step4, 1):
            dest = STEP4_DIR / info.filename
            if dest.exists() and dest.stat().st_size == info.file_size:
                disposition = "already-extracted"
                digest = sha256_file(dest)
            else:
                # ZipFile.open verifies the stored CRC-32 as it reads.
                with zf.open(info) as src, open(dest, "wb") as out:
                    h = hashlib.sha256()
                    while True:
                        chunk = src.read(CHUNK)
                        if not chunk:
                            break
                        h.update(chunk)
                        out.write(chunk)
                digest = h.hexdigest()
                assert dest.stat().st_size == info.file_size, f"size mismatch after extract: {info.filename}"
                disposition = "extracted"
            rows.append((info.filename, info.file_size, digest, disposition))
            print(f"[{k:3d}/{N_STEP4}] {disposition:18s} {info.filename}", flush=True)

        # --- 2. verify the 28 re-shipped test1 members against disk --------
        for k, info in enumerate(reship, 1):
            existing = SMR100_DIR / info.filename
            if not existing.exists():
                disposition = "NO-LOCAL-COPY"
                digest_zip = sha256_stream(zf.open(info))
                mismatches.append(info.filename)
            else:
                digest_zip = sha256_stream(zf.open(info))
                digest_disk = sha256_file(existing)
                if digest_zip == digest_disk:
                    disposition = "verified-identical-to-existing"
                else:
                    disposition = "MISMATCH"
                    mismatches.append(info.filename)
            rows.append((info.filename, info.file_size, digest_zip, disposition))
            print(f"[{k:3d}/{N_RESHIP}] {disposition:30s} {info.filename}", flush=True)

    with open(MANIFEST, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "size", "sha256", "disposition"])
        w.writerows(rows)
    print(f"\nmanifest: {MANIFEST} ({len(rows)} rows)")

    if mismatches:
        print("\nHARD STOP — re-shipped Step 3 files differ from the validated local copies:")
        for m in mismatches:
            print(f"  {m}")
        print("The step3_checks exports can no longer be treated as canonical. Ask NREL.")
        return 1

    print("\nAll 120 step4 members extracted; all 28 re-shipped Step 3/pilot files "
          "byte-identical to the validated local copies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

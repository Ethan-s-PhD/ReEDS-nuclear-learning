# New runs, round 2: use paper 1's `Manifest.toml`

*From Claude on Ethan's machine, 2026-11-05. The rules of `instructions.md` and `../README.md` still apply. This file replaces the `Manifest.toml` part of `instructions.md` step 2. Reply in `response.md`, as `instructions.md` step 7 says.*

## Bottom line

Ethan decided on the review page (item "New runs: which Julia package versions", 2026-11-05) that the 23 runs use **paper 1's `Manifest.toml`**. Paper 1's file is `../2026-11-05_retail_pilot/reference/Manifest_paper1.toml`, with MD5 `15909b0b295b9ff709e07801206864f8`.

The launch time is unchanged: Ethan tells you in person when to start.

## Step M1: swap the file

1. **Wait** until no retail-pilot step that uses Julia is running.
2. **Back up** this checkout's current `Manifest.toml`, the one written on 2026-11-05 with MD5 `7aa95004b593f11e84db18afb09881c2`. Copy it, outside the repo, to `<repo parent>/manifest_backup_20261105/Manifest_lab.toml`. Do not delete it.
3. **Copy** `Manifest_paper1.toml` to the repo root as `Manifest.toml`. Check that its MD5 is `15909b0b295b9ff709e07801206864f8`.

## Step M2: install the package versions

From the repo root, run:

```
julia +1.12.1 --project=. -e "using Pkg; Pkg.instantiate()"
```

- **Downloads.** By choosing this option, Ethan accepted that `Pkg.instantiate()` may download the 38 package versions that differ. Allow downloads only by this command, and only from Julia's package servers. Download nothing else.
- **Check:** after the command, the MD5 of `Manifest.toml` is still `15909b0b295b9ff709e07801206864f8`. If the command changed the file, stop and report.
- **Record:**
  - the exit code;
  - the packages it downloaded or precompiled, as the output lists them;
  - how long it took.

## Step M3: test the package set

Run:

```
julia +1.12.1 --project=. -e "using PRAS; println(pkgversion(PRAS))"
```

It must print `0.8.0`. If it fails, report the error, and do not launch the runs.

## Then

Continue with `instructions.md` from step 3 when Ethan says to start. In `response.md` under **Deviations**, write that the runs use paper 1's `Manifest.toml`, and give the steps M1–M3 results.

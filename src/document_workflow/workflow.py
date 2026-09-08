"""Document discovery, copying, and manifest generation."""

from __future__ import annotations

import csv
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from .core import SUPPORTED_EXTENSIONS, Rules, classify_text, extract_text


@dataclass(frozen=True)
class ManifestRecord:
    source: str
    category: str
    destination: str
    status: str
    message: str = ""


@dataclass(frozen=True)
class ProcessSummary:
    copied: int
    skipped: int
    errors: int
    records: tuple[ManifestRecord, ...]


def _available_destination(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    number = 2
    while candidate.exists():
        source = Path(filename)
        candidate = directory / f"{source.stem}-{number}{source.suffix}"
        number += 1
    return candidate


def _write_manifests(output: Path, summary: ProcessSummary) -> None:
    output_resolved = output.resolve()
    manifest_json_path = output / "manifest.json"
    manifest_csv_path = output / "manifest.csv"
    
    if manifest_json_path.is_symlink():
        raise ValueError("manifest.json is a symlink; refusing to write")
    if manifest_csv_path.is_symlink():
        raise ValueError("manifest.csv is a symlink; refusing to write")
    
    manifest_json_resolved = manifest_json_path.resolve()
    manifest_csv_resolved = manifest_csv_path.resolve()
    
    if not str(manifest_json_resolved).startswith(str(output_resolved)):
        raise ValueError("manifest.json would be written outside output directory")
    if not str(manifest_csv_resolved).startswith(str(output_resolved)):
        raise ValueError("manifest.csv would be written outside output directory")
    
    payload = {
        "summary": {"copied": summary.copied, "skipped": summary.skipped, "errors": summary.errors},
        "records": [asdict(record) for record in summary.records],
    }
    manifest_json_resolved.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with manifest_csv_resolved.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["source", "category", "destination", "status", "message"]
        )
        writer.writeheader()
        writer.writerows(asdict(record) for record in summary.records)


def process_documents(
    input_dir: Path, output_dir: Path, rules: Rules, *, dry_run: bool = False
) -> ProcessSummary:
    """Recursively classify and copy supported documents."""
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
    records: list[ManifestRecord] = []
    reserved: set[Path] = set()
    for source in sorted(path for path in input_dir.rglob("*") if path.is_file()):
        relative = str(source.relative_to(input_dir))
        if source.is_symlink():
            records.append(
                ManifestRecord(relative, "", "", "error", "Symbolic links are not processed")
            )
            continue
        if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
            records.append(ManifestRecord(relative, "", "", "unsupported", "Unsupported file type"))
            continue
        try:
            text = extract_text(source)
            category = classify_text(text, rules)
            category_dir = output_dir / category
            category_dir_resolved = category_dir.resolve()
            
            if category_dir.is_symlink():
                raise ValueError(f"Category directory {category} is a symlink; refusing to copy")
            if not str(category_dir_resolved).startswith(str(output_dir.resolve())):
                raise ValueError(f"Category {category} would write outside output directory")
            
            destination = _available_destination(category_dir, source.name)
            destination_resolved = destination.resolve()
            
            if not str(destination_resolved).startswith(str(output_dir.resolve())):
                raise ValueError(f"Destination would be written outside output directory")
            
            while destination in reserved:
                original = Path(source.name)
                number = 2
                while category_dir / f"{original.stem}-{number}{original.suffix}" in reserved:
                    number += 1
                destination = category_dir / f"{original.stem}-{number}{original.suffix}"
                destination_resolved = destination.resolve()
                if not str(destination_resolved).startswith(str(output_dir.resolve())):
                    raise ValueError(f"Destination {original.stem}-{number}{original.suffix} would be written outside output directory")
            
            reserved.add(destination)
            status = "planned" if dry_run else "copied"
            if not dry_run:
                category_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            records.append(
                ManifestRecord(
                    source=relative,
                    category=category,
                    destination=str(destination.relative_to(output_dir)),
                    status=status,
                )
            )
        except (OSError, UnicodeError, ValueError) as error:
            records.append(ManifestRecord(relative, "", "", "error", str(error)))
    copied = sum(record.status == "copied" for record in records)
    skipped = sum(record.status == "unsupported" for record in records)
    errors = sum(record.status == "error" for record in records)
    summary = ProcessSummary(copied, skipped, errors, tuple(records))
    if not dry_run:
        _write_manifests(output_dir, summary)
    return summary

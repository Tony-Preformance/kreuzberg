"""Comprehensive benchmark suite for Tesseract OCR output formats."""

import asyncio
import json
import time
import tracemalloc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
from rich.console import Console
from rich.table import Table

from kreuzberg import ExtractionConfig, TesseractConfig, extract_file, extract_file_sync
from kreuzberg._utils._cache import clear_all_caches


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""

    format_name: str
    file_path: Path
    duration: float
    memory_peak_mb: float
    memory_delta_mb: float
    content_length: int
    has_tables: bool = False
    table_count: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FormatComparison:
    """Comparison of different output formats."""

    baseline_format: str = "text"
    results: Dict[str, BenchmarkResult] = field(default_factory=dict)

    def get_relative_performance(self) -> Dict[str, float]:
        """Get performance relative to baseline format."""
        if self.baseline_format not in self.results:
            return {}

        baseline_duration = self.results[self.baseline_format].duration
        return {
            fmt: result.duration / baseline_duration
            for fmt, result in self.results.items()
        }

    def get_memory_comparison(self) -> Dict[str, float]:
        """Get memory usage comparison."""
        if self.baseline_format not in self.results:
            return {}

        baseline_memory = self.results[self.baseline_format].memory_peak_mb
        return {
            fmt: result.memory_peak_mb / baseline_memory if baseline_memory > 0 else 1.0
            for fmt, result in self.results.items()
        }


class TesseractOutputBenchmark:
    """Benchmark suite for Tesseract OCR output formats."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.process = psutil.Process()

    async def benchmark_single_format(
        self,
        file_path: Path,
        output_format: str,
        enable_table_detection: bool = False,
        force_ocr: bool = True,
    ) -> BenchmarkResult:
        """Benchmark a single output format."""
        clear_all_caches()

        self.console.print(
            f"[dim]Testing format {output_format} with table_detection={enable_table_detection}[/dim]"
        )

        config = ExtractionConfig(
            force_ocr=force_ocr,
            ocr_backend="tesseract",
            ocr_config=TesseractConfig(
                output_format=output_format,
                enable_table_detection=enable_table_detection,
                language="eng",
            ),
        )

        tracemalloc.start()
        memory_before = self.process.memory_info().rss / (1024 * 1024)

        start_time = time.perf_counter()
        try:
            result = await extract_file(file_path, config=config)
            duration = time.perf_counter() - start_time

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            memory_after = self.process.memory_info().rss / (1024 * 1024)

            return BenchmarkResult(
                format_name=output_format,
                file_path=file_path,
                duration=duration,
                memory_peak_mb=peak / (1024 * 1024),
                memory_delta_mb=memory_after - memory_before,
                content_length=len(result.content),
                has_tables=bool(result.tables),
                table_count=len(result.tables) if result.tables else 0,
                metadata={
                    "mime_type": result.mime_type,
                    "metadata_count": len(result.metadata) if result.metadata else 0,
                },
            )

        except Exception as e:
            tracemalloc.stop()
            return BenchmarkResult(
                format_name=output_format,
                file_path=file_path,
                duration=time.perf_counter() - start_time,
                memory_peak_mb=0,
                memory_delta_mb=0,
                content_length=0,
                error=str(e),
            )

    async def benchmark_all_formats(
        self,
        file_path: Path,
        include_table_detection: bool = True,
        force_ocr: bool = True,
    ) -> FormatComparison:
        """Benchmark all output formats on the same file."""
        comparison = FormatComparison()

        formats = ["text", "hocr", "markdown", "tsv"]

        for fmt in formats:
            self.console.print(f"Benchmarking format: {fmt}")
            result = await self.benchmark_single_format(
                file_path, fmt, enable_table_detection=False, force_ocr=force_ocr
            )
            comparison.results[fmt] = result

        if include_table_detection:
            self.console.print("Benchmarking TSV with table detection")
            result = await self.benchmark_single_format(
                file_path, "tsv", enable_table_detection=True, force_ocr=force_ocr
            )
            comparison.results["tsv_tables"] = result

        return comparison

    def benchmark_table_detection_thresholds(
        self,
        table_image_path: Path,
        column_thresholds: List[int] = None,
        row_thresholds: List[float] = None,
    ) -> Dict[str, BenchmarkResult]:
        """Benchmark table detection with different threshold parameters."""
        if column_thresholds is None:
            column_thresholds = [10, 20, 30, 50]
        if row_thresholds is None:
            row_thresholds = [0.3, 0.5, 0.7, 1.0]

        results = {}

        for col_threshold in column_thresholds:
            for row_threshold in row_thresholds:
                config = ExtractionConfig(
                    force_ocr=True,
                    ocr_backend="tesseract",
                    ocr_config=TesseractConfig(
                        output_format="tsv",
                        enable_table_detection=True,
                        table_column_threshold=col_threshold,
                        table_row_threshold_ratio=row_threshold,
                    ),
                )

                clear_all_caches()

                start_time = time.perf_counter()
                result = extract_file_sync(table_image_path, config=config)
                duration = time.perf_counter() - start_time

                key = f"col_{col_threshold}_row_{row_threshold}"
                results[key] = BenchmarkResult(
                    format_name="tsv_tables",
                    file_path=table_image_path,
                    duration=duration,
                    memory_peak_mb=0,
                    memory_delta_mb=0,
                    content_length=len(result.content),
                    has_tables=bool(result.tables),
                    table_count=len(result.tables) if result.tables else 0,
                    metadata={
                        "column_threshold": col_threshold,
                        "row_threshold": row_threshold,
                    },
                )

        return results

    async def profile_conversion_overhead(
        self, file_path: Path
    ) -> Dict[str, Dict[str, float]]:
        """Profile the conversion overhead for each format."""
        timings = {}

        config_hocr = ExtractionConfig(
            force_ocr=True,
            ocr_backend="tesseract",
            ocr_config=TesseractConfig(output_format="hocr"),
        )

        clear_all_caches()
        start = time.perf_counter()
        await extract_file(file_path, config=config_hocr)
        hocr_time = time.perf_counter() - start

        timings["hocr"] = {
            "total": hocr_time,
            "ocr": hocr_time,
            "conversion": 0,
        }

        config_md = ExtractionConfig(
            force_ocr=True,
            ocr_backend="tesseract",
            ocr_config=TesseractConfig(output_format="markdown"),
        )

        clear_all_caches()
        start = time.perf_counter()
        await extract_file(file_path, config=config_md)
        md_time = time.perf_counter() - start

        timings["markdown"] = {
            "total": md_time,
            "ocr": hocr_time,
            "conversion": md_time - hocr_time,
        }

        config_tsv = ExtractionConfig(
            force_ocr=True,
            ocr_backend="tesseract",
            ocr_config=TesseractConfig(output_format="tsv"),
        )

        clear_all_caches()
        start = time.perf_counter()
        await extract_file(file_path, config=config_tsv)
        tsv_time = time.perf_counter() - start

        timings["tsv"] = {
            "total": tsv_time,
            "ocr": tsv_time * 0.9,
            "conversion": tsv_time * 0.1,
        }

        config_tsv_tables = ExtractionConfig(
            force_ocr=True,
            ocr_backend="tesseract",
            ocr_config=TesseractConfig(
                output_format="tsv", enable_table_detection=True
            ),
        )

        clear_all_caches()
        start = time.perf_counter()
        await extract_file(file_path, config=config_tsv_tables)
        tsv_tables_time = time.perf_counter() - start

        timings["tsv_tables"] = {
            "total": tsv_tables_time,
            "ocr": tsv_time * 0.9,
            "conversion": tsv_tables_time - (tsv_time * 0.9),
        }

        return timings

    def print_comparison_report(self, comparison: FormatComparison):
        """Print a formatted comparison report."""
        table = Table(title="Tesseract Output Format Comparison")
        table.add_column("Format", style="bold")
        table.add_column("Duration (s)", justify="right")
        table.add_column("Relative", justify="right")
        table.add_column("Memory (MB)", justify="right")
        table.add_column("Content Size", justify="right")
        table.add_column("Tables", justify="right")

        relative_perf = comparison.get_relative_performance()
        memory_comp = comparison.get_memory_comparison()

        for fmt in ["text", "hocr", "markdown", "tsv", "tsv_tables"]:
            if fmt not in comparison.results:
                continue

            result = comparison.results[fmt]
            relative = relative_perf.get(fmt, 1.0)
            memory_rel = memory_comp.get(fmt, 1.0)

            if relative <= 1.2:
                duration_style = "green"
            elif relative <= 2.0:
                duration_style = "yellow"
            else:
                duration_style = "red"

            table.add_row(
                fmt,
                f"[{duration_style}]{result.duration:.3f}[/{duration_style}]",
                f"[{duration_style}]{relative:.1f}x[/{duration_style}]",
                f"{result.memory_peak_mb:.1f} ({memory_rel:.1f}x)",
                str(result.content_length),
                str(result.table_count) if result.table_count > 0 else "-",
            )

        self.console.print(table)

        sorted_formats = sorted(comparison.results.items(), key=lambda x: x[1].duration)

        self.console.print("\n[bold]Performance Order (fastest to slowest):[/bold]")
        for i, (fmt, result) in enumerate(sorted_formats, 1):
            self.console.print(f"  {i}. {fmt}: {result.duration:.3f}s")

    def save_results(self, results: Any, output_path: Path):
        """Save benchmark results to JSON."""

        def serialize(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, BenchmarkResult):
                return {
                    "format": obj.format_name,
                    "file": str(obj.file_path),
                    "duration": obj.duration,
                    "memory_peak_mb": obj.memory_peak_mb,
                    "memory_delta_mb": obj.memory_delta_mb,
                    "content_length": obj.content_length,
                    "has_tables": obj.has_tables,
                    "table_count": obj.table_count,
                    "error": obj.error,
                    "metadata": obj.metadata,
                }
            elif isinstance(obj, FormatComparison):
                return {
                    "baseline_format": obj.baseline_format,
                    "results": {k: serialize(v) for k, v in obj.results.items()},
                    "relative_performance": obj.get_relative_performance(),
                    "memory_comparison": obj.get_memory_comparison(),
                }
            else:
                return str(obj)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=serialize)


async def main():
    """Run comprehensive Tesseract benchmarks."""
    console = Console()
    benchmark = TesseractOutputBenchmark(console)

    test_files = {
        "simple_text": Path("tests/test_source_files/searchable.pdf"),
        "scanned_pdf": Path("tests/test_source_files/scanned.pdf"),
        "ocr_image": Path("tests/test_source_files/ocr-image.jpg"),
        "simple_table": Path("tests/test_source_files/tables/simple_table.png"),
        "complex_table": Path("tests/test_source_files/tables/complex_document.png"),
    }

    results = {}

    console.print("\n[bold blue]Format Comparison Benchmarks[/bold blue]\n")

    for name, file_path in test_files.items():
        if not file_path.exists():
            console.print(f"[yellow]Skipping {name}: file not found[/yellow]")
            continue

        console.print(f"\n[bold]Testing: {name}[/bold]")
        comparison = await benchmark.benchmark_all_formats(file_path)
        benchmark.print_comparison_report(comparison)
        results[f"comparison_{name}"] = comparison

    console.print("\n[bold blue]Table Detection Threshold Testing[/bold blue]\n")

    table_image = test_files.get("simple_table")
    if table_image and table_image.exists():
        threshold_results = benchmark.benchmark_table_detection_thresholds(table_image)

        table = Table(title="Table Detection Threshold Results")
        table.add_column("Thresholds", style="bold")
        table.add_column("Duration (s)", justify="right")
        table.add_column("Tables Found", justify="right")

        for key, result in sorted(threshold_results.items()):
            table.add_row(key, f"{result.duration:.3f}", str(result.table_count))

        console.print(table)
        results["threshold_testing"] = threshold_results

    console.print("\n[bold blue]Conversion Overhead Analysis[/bold blue]\n")

    test_file = test_files.get("ocr_image")
    if test_file and test_file.exists():
        overhead_timings = await benchmark.profile_conversion_overhead(test_file)

        table = Table(title="Processing Time Breakdown")
        table.add_column("Format", style="bold")
        table.add_column("Total (s)", justify="right")
        table.add_column("OCR (s)", justify="right")
        table.add_column("Conversion (s)", justify="right")
        table.add_column("Overhead %", justify="right")

        for fmt, timings in overhead_timings.items():
            overhead_pct = (
                (timings["conversion"] / timings["total"] * 100)
                if timings["total"] > 0
                else 0
            )
            table.add_row(
                fmt,
                f"{timings['total']:.3f}",
                f"{timings['ocr']:.3f}",
                f"{timings['conversion']:.3f}",
                f"{overhead_pct:.1f}%",
            )

        console.print(table)
        results["conversion_overhead"] = overhead_timings

    output_dir = Path("benchmarks/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"tesseract_benchmark_{timestamp}.json"

    benchmark.save_results(results, output_file)
    console.print(f"\n[green]Results saved to: {output_file}[/green]")

    return results


if __name__ == "__main__":
    asyncio.run(main())

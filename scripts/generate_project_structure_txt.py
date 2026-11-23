import os
from pathlib import Path

def generate_structure():
    root = Path(".")
    output_path = Path("RAG_BPS_DEMAK_AUDIT_EXPORT/PROJECT_STRUCTURE.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_descriptions = {
        "main.py": "Master Pipeline Orchestrator (CLI modes: statis, all, test, pdf, query)",
        "app.py": "Legacy Streamlit Web Interface (Alternative GUI)",
        "Dockerfile": "Containerization build specification (Multi-stage Node+Python)",
        "docker-compose.yml": "Docker Compose service configuration",
        "requirements.txt": "Python dependencies specification",
        "README.md": "Core project documentation and setup overview",
        "deploy.sh": "Linux production deployment script",
        "run_dashboard.bat": "Windows single-click launcher for backend & frontend",
        "run_dashboard.sh": "Linux/macOS launcher script",
        "run_ingestion.py": "Standalone ingestion script runner",
        "batch_process_10_publications.py": "Batch processing utility for 10 initial publications",
        "test_download_and_convert.py": "Verification test script for download & conversion pipeline",
        "test_run.py": "Integration test runner script",
        "skills-lock.json": "Agent skills lockfile",
        ".env.example": "Template configuration for environment variables (Non-secret)",
        ".gitignore": "Git exclusion rules",
        ".dockerignore": "Docker build exclusion rules",
        "LAPORAN_AUDIT_RAG_BPS_DEMAK.docx": "Comprehensive Technical Audit Report in Microsoft Word format",
        "LAPORAN_FINAL_RAG_BPS_DEMAK.md": "Master technical report in Markdown format"
    }

    dir_descriptions = {
        "api": "FastAPI Web Controllers, Routers (auth, ingestion, data_viewer, system_telemetry), Schemas",
        "chatbot": "Core RAG Chatbot Engine (bot.py, rag_feeder.py, llm_client.py, memory.py, prompt_templates.py)",
        "config": "System and Database Configuration (settings.py, database.py)",
        "database": "NoSQL JSON storage, SQLite registries, and legacy ChromaDB fallback",
        "data_publikasi": "Official BPS Demak PDF Publications Archive (2007-2026)",
        "docs": "Technical Documentation, Engineering Guides, and Forensic Audit Documents",
        "doc": "Additional Documentation and Architecture Notes",
        "frontend": "Modern Vue 3 + Tailwind CSS Single Page Application (Dual-Portal UI)",
        "logs": "Application Runtime Log Files (Loguru daily rotation)",
        "modules": "Core Processing Pipelines (crawler, extraction, structuring, vectorization, storage, retrieval)",
        "scripts": "Database initialization, migration, and maintenance utilities",
        "tests": "Automated Test Suite (24 test cases, golden benchmarks, pytest)",
        ".agents": "Antigravity Agent Skills & Automation specifications",
        "RAG_BPS_DEMAK_AUDIT_EXPORT": "Output export folder for external audit packaging"
    }

    lines = []
    lines.append("=" * 85)
    lines.append("PROJECT STRUCTURE & FILE INVENTORY: RAG BPS KABUPATEN DEMAK (RAG3321)")
    lines.append("PostgreSQL 15 + pgvector 0.8.1 | FastAPI | Vue 3 | SentenceTransformers | Gemini")
    lines.append("=" * 85)
    lines.append("")
    lines.append(f"Root Directory: {root.resolve()}")
    lines.append("")

    for item in sorted(root.iterdir()):
        if item.name.startswith(".git") and item.name != ".gitignore":
            continue
        if item.name == "RAG_BPS_DEMAK_AUDIT_EXPORT":
            continue

        if item.is_dir():
            desc = dir_descriptions.get(item.name, "Directory")
            sub_count = sum(1 for _ in item.iterdir()) if item.exists() else 0
            lines.append(f"\n[DIR]  {item.name}/  ({sub_count} direct items)")
            lines.append(f"       Fungsi: {desc}")
            
            # Print important sub-items
            if item.name in ["api", "chatbot", "config", "modules", "scripts", "tests", "docs"]:
                for sub in sorted(item.iterdir()):
                    if sub.name.startswith("__pycache__"):
                        continue
                    if sub.is_dir():
                        lines.append(f"         ├── [DIR]  {sub.name}/")
                        for ssub in sorted(sub.iterdir())[:8]:
                            if not ssub.name.startswith("__pycache__"):
                                sz_kb = ssub.stat().st_size / 1024 if ssub.is_file() else 0
                                lines.append(f"         │     ├── {ssub.name:30} ({sz_kb:8.1f} KB)")
                    else:
                        sz_kb = sub.stat().st_size / 1024
                        lines.append(f"         ├── {sub.name:35} ({sz_kb:8.1f} KB)")
            elif item.name == "frontend":
                for sub in sorted(item.iterdir()):
                    if sub.name == "node_modules":
                        lines.append(f"         ├── [DIR]  node_modules/ (Excluded from export - 123 MB)")
                    elif sub.is_dir():
                        lines.append(f"         ├── [DIR]  {sub.name}/")
                        for ssub in sorted(sub.iterdir()):
                            sz_kb = ssub.stat().st_size / 1024 if ssub.is_file() else 0
                            lines.append(f"         │     ├── {ssub.name:30} ({sz_kb:8.1f} KB)")
                    else:
                        sz_kb = sub.stat().st_size / 1024
                        lines.append(f"         ├── {sub.name:35} ({sz_kb:8.1f} KB)")
            elif item.name == "database":
                for sub in sorted(item.iterdir()):
                    if sub.is_dir():
                        lines.append(f"         ├── [DIR]  {sub.name}/")
                    else:
                        sz_mb = sub.stat().st_size / (1024*1024)
                        lines.append(f"         ├── {sub.name:35} ({sz_mb:8.2f} MB)")
            elif item.name == "data_publikasi":
                lines.append(f"         ├── demak/ (586 PDF publications partitioned by year 2007-2026, 2.69 GB total)")

        else:
            desc = file_descriptions.get(item.name, "File")
            sz_kb = item.stat().st_size / 1024
            lines.append(f"[FILE] {item.name:35} | {sz_kb:8.1f} KB | {desc}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated {output_path}")

if __name__ == "__main__":
    generate_structure()

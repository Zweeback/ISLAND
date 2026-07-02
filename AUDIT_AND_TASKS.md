# 🔍 ISLAND Monorepo - Audit & Task Assignment for Jules

**Date:** 2026-06-23
**Status:** Ready for Implementation
**Priority:** HIGH

---

## 📊 AUDIT REPORT

### Current State Analysis

| Repo | Size | Status | Value | Action |
|------|------|--------|-------|--------|
| **alice** | Minimal | Placeholder | ⭐ | MOVE to Input/projects/alice/ |
| **benjamin-carl-zwieback** | Medium | Production | ⭐⭐⭐ | MOVE to Input/projects/benjamin-carl/ |
| **bentropie-main** | Small | AI Studio | ⭐⭐ | MOVE to Input/projects/bentropie/ |
| **dna** | Small | AI Studio Template | ⭐⭐ | MOVE to Input/projects/dna/ |
| **feednoodle** | Small | AI Studio (Browser) | ⭐⭐ | MOVE to Input/projects/feednoodle/ |
| **promptdex** | Small | Prompt Mgmt | ⭐ | MOVE to Input/projects/promptdex/ |
| **rag** | LARGE | Data Heavy | ⭐⭐⭐ | EXTRACT CODE + MOVE to Input/archive/rag-data/ |
| **rag-index** | Medium | Production Framework | ⭐⭐⭐⭐ | MOVE to Input/projects/rag-index/ |
| **ragonnnn** | Small | RAG Variant | ⭐ | MOVE to Input/projects/ragonnnn/ |
| **workspace** | Minimal | Dev Env | ⭐ | MOVE to Input/projects/workspace/ |

### Reference Materials
- **grok-prompts (xAI)** - External reference (4.1K ⭐) → DOCUMENT in Input/references/

### Summary
- **Total Projects:** 10 personal repos
- **Projects to consolidate:** 10
- **Reference materials:** 1 (external)
- **Estimated scope:** 15-20 files to process

---

## ✅ TASKS FOR JULES

### Phase 1: Structure Setup (Priority: CRITICAL)
**Deadline:** Immediate

#### Task 1.1: Create Directory Structure
```
Input/
├── projects/
│   ├── alice/
│   ├── benjamin-carl/
│   ├── bentropie/
│   ├── dna/
│   ├── feednoodle/
│   ├── promptdex/
│   ├── rag-index/
│   ├── ragonnnn/
│   └── workspace/
├── archive/
│   ├── rag-data/
│   │   ├── pdfs/
│   │   ├── chat-exports/
│   │   └── documents/
│   └── legacy/
├── references/
│   └── grok-prompts/
└── docs/
    └── setup-guide.md
```

**Requirements:**
- Create all directories
- Add .gitkeep files if empty
- Commit message: "Phase 1: Initialize monorepo directory structure"

---

### Phase 2: Repository Migration (Priority: HIGH)

#### Task 2.1: Migrate `benjamin-carl-zwieback`
**Status:** PRODUCTION CODE
**Action:** Full migration (keep all files including package.json, tsconfig.json, src/, etc.)
**Target:** `Input/projects/benjamin-carl/`
**Files to include:**
- server.ts
- package.json / package-lock.json
- tsconfig.json
- vite.config.ts
- src/
- firebase-applet-config.json
- .env.example

**Commit:** "Add: benjamin-carl project - Firebase/Node.js app"

---

#### Task 2.2: Migrate `rag-index`
**Status:** PRODUCTION FRAMEWORK
**Action:** Full migration
**Target:** `Input/projects/rag-index/`
**Files to include:**
- ARCHITECTURE.txt
- START_HERE.md
- SETUP_GUIDE_COMPLETE.md
- *.html files (alice_browser_free, alice_companion, etc.)
- *.py files (app.py, setup_complete.py, etc.)
- requirements.txt
- data/
- scripts/

**Commit:** "Add: rag-index - RAG framework & production apps"

---

#### Task 2.3: Migrate `dna` + `feednoodle`
**Status:** AI STUDIO TEMPLATES
**Action:** Full migration (keep template structure)
**Target:** 
- `Input/projects/dna/`
- `Input/projects/feednoodle/`
**Files to include:** README.md + template files

**Commit:** "Add: dna & feednoodle - Google Gemini AI Studio projects"

---

#### Task 2.4: Migrate `alice`, `bentropie`, `promptdex`, `ragonnnn`, `workspace`
**Status:** SUPPORTING PROJECTS
**Action:** Full migration
**Target:** `Input/projects/{project-name}/`
**Commit:** "Add: supporting projects - alice, bentropie, promptdex, ragonnnn, workspace"

---

### Phase 3: Data Consolidation (Priority: MEDIUM)

#### Task 3.1: Extract & Organize RAG Data
**Status:** LARGE DATA ARCHIVE
**Action:** Extract useful data, organize intelligently
**Source:** `Zweeback/rag` (hundreds of files)
**Target:** `Input/archive/rag-data/`

**Organize as:**
```
rag-data/
├── pdfs/              (All .pdf files)
├── chat-exports/      (All ._chat*.txt & conversations.json)
├── documentation/     (*.md files with content)
├── code/              (alice_autoloop.py, codex_*.py, etc.)
└── raw-exports/       (Everything else)
```

**Commit:** "Add: RAG data archive - PDFs, chat exports, documentation"

---

### Phase 4: Reference Materials (Priority: LOW)

#### Task 4.1: Document xAI Grok Prompts
**Status:** EXTERNAL REFERENCE
**Target:** `Input/references/GROK_PROMPTS.md`
**Action:** Create summary document

**Content:**
```markdown
# xAI Grok System Prompts Reference

Source: https://github.com/xai-org/grok-prompts
License: AGPL-3.0

## Prompts Included
- Grok 4 System Prompt (v8)
- Grok 3 System Prompt
- Grok 4.1 Variants (thinking/non-thinking)
- Safety Instructions
- API Integration Prompts

## Use Cases
- Reference for AI safety patterns
- Prompt engineering best practices
- Production LLM deployment examples
```

**Commit:** "Add: Grok prompts reference documentation"

---

### Phase 5: Documentation & Cleanup (Priority: MEDIUM)

#### Task 5.1: Create Comprehensive README
**Target:** `Input/README.md`
**Content:**
- Overview of all projects
- Quick start guide
- Architecture diagram (if applicable)
- Links to individual project docs

**Commit:** "Add: Input folder comprehensive README"

#### Task 5.2: Create Project Index
**Target:** `Input/PROJECTS.md`
**Content:**
- Project summaries
- Tech stacks
- Dependencies
- Known issues

**Commit:** "Add: Project inventory & documentation"

---

## 🎯 Success Criteria

- [ ] All 10 projects migrated to Input/projects/
- [ ] RAG data organized in Input/archive/
- [ ] References documented
- [ ] All commits pushed
- [ ] No broken file references
- [ ] Directory structure clean & organized
- [ ] README files in each project folder

---

## ⚠️ Important Notes

1. **Original repos:** Should be deleted manually after migration (not automated)
2. **Git history:** Migration copies current state only (not full commit history)
3. **Sensitive files:** Check .env.example files - DO NOT include actual .env files
4. **Large files:** RAG PDFs may need compression or separate handling
5. **Dependencies:** Each project should maintain its own requirements.txt/package.json

---

## 📅 Timeline

- **Phase 1:** 5 min (Structure)
- **Phase 2:** 15 min (Repository migration)
- **Phase 3:** 10 min (Data consolidation)
- **Phase 4:** 5 min (References)
- **Phase 5:** 10 min (Documentation)

**Total:** ~45 minutes

---

## 🚀 Next Steps

1. Jules executes Phase 1-5 in order
2. Review consolidated ISLAND repo
3. Test all project documentation links
4. Verify no files missing
5. Delete original 10 repositories (manual via GitHub UI)
6. Archive complete!

---

**Report Generated:** 2026-06-23 23:20 UTC
**Assigned To:** Jules (Copilot Agent)
**Status:** AWAITING EXECUTION
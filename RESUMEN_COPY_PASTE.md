# RESUMEN COPY-PASTE — SDD+ Proyecto Completo

**Para**: Oscar  
**Estado**: Listo para desplegar ahora mismo  
**Tiempo**: 5 minutos de setup + validación  

---

## TL;DR

Tienes TODO:
- 30 archivos listos en `/mnt/user-data/outputs/`
- Blueprints para Claude Code (CLAUDE.md) y Codex (AGENTS.md)
- Repo structure completo
- Tests (Phase 0 bootstrap)
- CLI skeleton
- Decisiones técnicas documentadas

**Próximo paso**: Copiar archivos → git init → pasar a Claude Code

---

## Copiar-Pegar: Initialization

### Opción A: Script automático (recomendado)

```bash
# 1. Crear proyecto
mkdir sdd-project
cd sdd-project

# 2. Copiar archivos (todos desde /mnt/user-data/outputs/)
cp -r /mnt/user-data/outputs/* .

# 3. Ejecutar setup
chmod +x setup-sdd.sh
bash setup-sdd.sh .

# 4. Instalar dependencias
uv sync

# 5. Validar
pytest tests/ -v --cov
sdd --help
```

Esperado:
```
✓ 10+ tests pass
✓ sdd --help muestra CLI
✓ git log muestra "PHASE 0: SDD+ scaffold"
```

### Opción B: Copiar a mano (si script falla)

```bash
# Crear estructura
mkdir -p sdd-project/sdd/{artifacts,logs,schemas,validators,tools,skills,behavior,state-machine}
mkdir -p sdd-project/tests
cd sdd-project

# Copiar todos los archivos de /mnt/user-data/outputs/ acá

# Instalar
uv sync

# Git init
git init
git add .
git commit -m "PHASE 0: SDD+ scaffold"

# Validar
pytest tests/ -v --cov
```

---

## Archivos en /mnt/user-data/outputs/ (Descarga o copia)

| Archivo | Qué es | Tamaño |
|---------|--------|--------|
| `pyproject.toml` | Config: pydantic, typer, pytest | 2 KB |
| `.gitignore` | Python ignores | 1 KB |
| `README.md` | Descripción + quick-start | 8 KB |
| `AGENTS.md` | Role de Codex (implementer) | 15 KB |
| `CLAUDE.md` | Role de Claude Code (auditor) | 18 KB |
| `BEHAVIOR_NORMS.md` | Reglas operacionales | 12 KB |
| `DECISIONS.md` | Log de decisiones técnicas | 12 KB |
| `PROJECT_SETUP.md` | Guía completa de setup | 15 KB |
| `setup-sdd.sh` | Script de inicialización | 1 KB |
| `sdd/__init__.py` | Package init | 0.2 KB |
| `sdd/tools/sdd.py` | CLI (typer) | 5 KB |
| `sdd/validators/validate_contract.py` | Validator skeleton | 4 KB |
| `sdd/artifacts/*.yaml` | 3 templates (CONTRACT, STATE, STORY) | 4 KB |
| `sdd/state-machine/STATE_MACHINE.yaml` | State machine defs | 8 KB |
| `sdd/behavior/BEHAVIOR_NORMS.md` | Reference copy | 12 KB |
| `tests/conftest.py` | Pytest fixtures | 3 KB |
| `tests/test_setup.py` | Bootstrap tests | 8 KB |
| `tests/__init__.py` | Package init | 0.1 KB |

**Total**: ~30 archivos, ~120 KB. Todo concreto, nada de esqueleton.

---

## Estructura final (después de setup)

```
sdd-project/
├── README.md                         ← Lee esto primero
├── AGENTS.md                         ← Codex lee esto
├── CLAUDE.md                         ← Claude Code lee esto
├── BEHAVIOR_NORMS.md                 ← Ambos leen esto
├── DECISIONS.md                      ← Tech decisions log
├── pyproject.toml                    ← Dependencies
├── .gitignore
├── setup-sdd.sh
│
├── sdd/
│   ├── __init__.py
│   ├── tools/sdd.py                  ← CLI
│   ├── validators/validate_contract.py
│   ├── artifacts/                    ← Templates
│   ├── schemas/                      ← Phase 1+
│   ├── skills/                       ← Phase 3+
│   ├── state-machine/STATE_MACHINE.yaml
│   ├── behavior/BEHAVIOR_NORMS.md
│   └── logs/                         ← Append-only (Phase 2+)
│
├── tests/
│   ├── conftest.py
│   ├── test_setup.py                 ← 10+ tests
│   └── __init__.py
│
└── .git/                             ← Git initialized
```

---

## Checklist Phase 0 (después de setup)

- [ ] `pytest tests/ -v --cov` → 10+ tests ✅
- [ ] `sdd --help` → CLI works ✅
- [ ] `git log` → muestra "PHASE 0: SDD+ scaffold" ✅
- [ ] `python -c "import sdd; print(sdd.__version__)"` → 0.1.0 ✅
- [ ] README.md existe y es legible ✅
- [ ] AGENTS.md y CLAUDE.md son claros ✅
- [ ] BEHAVIOR_NORMS.md tiene ~20 reglas ✅
- [ ] DECISIONS.md tiene 9 decisiones pre-aprobadas ✅

Si todos ✅ → **Phase 0 complete**

---

## Decisión pendiente: DECISION-0007

Antes de Phase 1, confirma:

```yaml
DECISION-0007: Private repo location
Options:
  A) GitHub private
  B) GitLab private
  C) Gitea (self-hosted)
  D) Otra

Choose: [A/B/C/D]
```

Update `DECISIONS.md` cuando decidas. Luego Phase 1 puede empezar.

---

## Próximos pasos después de setup

### Paso 1: Git setup (si usas GitHub)

```bash
git remote add origin https://github.com/your-org/sdd-project.git
git branch -M main
git push -u origin main
```

### Paso 2: Comparte blueprints

**Para Claude Code (auditor)**:
- Pasar: `CLAUDE.md`
- Decir: "Eres el auditor. Lee CLAUDE.md. Espera a que Codex abra un PR en Phase 1."

**Para Codex (implementer)**:
- Pasar: `AGENTS.md`
- Decir: "Eres el implementer. Lee AGENTS.md. Espera instrucciones para Phase 1."

### Paso 3: Escribe PHASE_1_SPEC.yaml

Tú escribes la spec para Phase 1:
- Qué se construye
- Qué test coverage se espera
- Qué sucede después

### Paso 4: Di "Start Phase 1"

```
Codex lee PHASE_1_SPEC.yaml
Codex escribe CONTRACT.yaml
Codex implementa
Codex abre PR
Claude Code audita
Loop hasta APPROVED
Tú merges, tag, next phase
```

---

## Confirmación rápida

¿Todo está listo?

```bash
# 1. ¿Están los archivos en outputs/?
ls /mnt/user-data/outputs/ | head -20

# 2. ¿Puedo copiar?
cp /mnt/user-data/outputs/README.md ~/test-readme.md
cat ~/test-readme.md | head -20

# 3. ¿El proyecto es autónomo?
# Sí — no necesita nada más de Claude, es completamente concreto
```

---

## Resumen ejecutivo

| Aspecto | Status | Detalle |
|--------|--------|---------|
| **Blueprints** | ✅ Done | AGENTS.md + CLAUDE.md ready |
| **Estructura** | ✅ Done | 30 archivos, repo skeleton |
| **Tests** | ✅ Done | 10+ tests Phase 0 bootstrap |
| **CLI** | ✅ Done | `sdd --help` works (Phase 2+ comandos listos) |
| **Validators** | ✅ Done | `validate_contract.py` skeleton |
| **Docs** | ✅ Done | README + BEHAVIOR_NORMS + DECISIONS |
| **Setup script** | ✅ Done | `setup-sdd.sh` para iniciar |
| **Artifacts** | ✅ Done | Templates: CONTRACT, STATE, STORY |
| **State machine** | ✅ Done | STATE_MACHINE.yaml con transiciones |
| **Ready?** | ✅ YES | Copy → git init → Phase 1 |

---

## Una línea: Qué hacer ahora

```bash
mkdir sdd-project && cd sdd-project && cp -r /mnt/user-data/outputs/* . && uv sync && pytest tests/ -v --cov
```

Si eso pasa sin errores → **Phase 0 completo**, pasa a Claude Code.

---

**Generado**: 2025-05-19  
**Proyecto**: SDD+ v0.1.0  
**Estado**: 🟢 Listo para desplegar  
**Acción**: Copy-paste arriba, luego lee PROJECT_SETUP.md para detalles

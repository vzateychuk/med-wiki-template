# med-wiki

Шаблон персональной медицинской wiki: правила агента, навыки, схемы страниц и словарь лабораторных синонимов.

Рабочие досье пациентов (`med-wiki-vovk`, `med-wiki-lena` и т.п.) подключают этот репозиторий как Git submodule в каталог `template/` и держат в корне символические ссылки:

| В корне patient-репо | Цель |
| --- | --- |
| `AGENTS.md` | `template/AGENTS.md` |
| `.agents/` | `template/.agents/` |
| `schema/` | `template/schema/` |
| `README.md` | `template/README.md` |

Данные пациента (`wiki/`, `raw/`) в шаблон не входят.

## Содержимое шаблона

- `AGENTS.md` — маршруты и правила агента
- `.agents/skills/` — ingest, lint, именование файлов
- `schema/templates/` — шаблоны страниц wiki
- `schema/metric-synonyms.yaml` — канон slug и синонимов лабораторных показателей

## Клон patient-репозитория

```bash
git clone --recurse-submodules <url-patient-repo>
```

Если клонировали без submodule:

```bash
git submodule update --init --recursive
```

## Обновить шаблон в patient-репо

После изменений в `med-wiki-template`:

```bash
cd <patient-repo>
git submodule update --remote --merge template
git add template (либо `git add .`, он включает в себя и обновление template)
git commit -m "chore: bump med-wiki-template"
git push
```

Правки канона (`AGENTS.md`, skills, `schema`, этот README) вносите в **med-wiki-template**, не в копии внутри patient-репо.

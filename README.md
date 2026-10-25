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

Правки канона (`AGENTS.md`, skills, `schema`, этот README) вносите в **отдельный клон med-wiki-template** (например `~/work/med-wiki`), не через symlink и не «внутри» `patient-repo/template/`.

`git add template` фиксирует только новый SHA шаблона. `git add .` тоже включит bump `template`, но заодно все прочие локальные правки в patient-репо (`wiki/` и т.д.) — для чистого bump лучше явный `git add template`.

## Случайно правили файлы внутри `template/`

Symlink из корня (`README.md` → `template/README.md` и т.п.) ведёт в submodule: правка «корневого» README — это правка файла **внутри** `template/`. Тогда `git submodule update --remote --merge template` часто падает:

```text
error: Your local changes to the following files would be overwritten by merge:
	README.md
Please commit your changes or stash them before you merge.
fatal: Unable to merge '...' in submodule path 'template'
```

В `git status` patient-репо при этом бывает `modified: template (modified content)`.

### Неверно

```bash
# из корня patient-репо — так submodule не очистить
git reset --hard template/
```

### Верно: выбросить случайные правки и подтянуть GitHub

Из корня patient-репо:

```bash
# что изменили внутри submodule
git -C template status
git -C template diff

# сбросить отслеживаемые файлы к HEAD submodule
git -C template reset --hard
# убрать неотслеживаемый мусор внутри template/, если был
git -C template clean -fd

# снова обновить с remote
git submodule update --remote --merge template

git add template
git commit -m "chore: bump med-wiki-template"
git push
```

`-C template` = выполнить команду так, будто текущий каталог — `template/`.  
`reset --hard` / `clean` внутри `template/` **не** трогают `wiki/` и `raw/` patient-репо.

### Если правки в template всё же нужны

Не `reset --hard`. Перенесите их в клон **med-wiki-template**: commit + push там, затем в patient-репо обычный bump (раздел выше).

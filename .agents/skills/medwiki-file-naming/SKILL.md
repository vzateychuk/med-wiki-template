---
name: medwiki-file-naming
description: Правила имён файлов в med-wiki - raw/docs, raw/images, raw/articles, страницы wiki. Use when creating, naming or checking a file name in med-wiki (ingest, saving a note or symptom, lint).
---

# Имена файлов

Единственный канон имён — этот навык и программа ниже. Другие навыки только вызывают программу и подставляют полученную строку в путь файла.

**Имя нового файла, не полученное от `naming.py`, — ошибка.** Существующие файлы в `raw/` не переименовываются; их имена проверяет только lint. Вручную имена не собирай и не меняй порядок частей: тип документа всегда сразу после даты (`<дата>_<тип>[-<уточнение>]`, не `<дата>_lor-consultation`).

Имя нового файла выбирай сам. Пользователя не спрашивай, кроме случая: в тексте меддокумента нет даты — без даты имя не построить. Тогда **предложи** наиболее правдоподобную дату (контекст чата, соседние файлы) и одним вопросом попроси подтвердить или поправить. Существующий файл не переименовываешь и не перезаписываешь: при занятом имени добавь уточнение (`disambiguator`).

## Инструмент именования

**Путь:** `.agents/skills/medwiki-file-naming/naming.py`

Программа сама проверяет дату, тип и slug. Агент не дублирует проверки вручную: передал параметры → получил одну строку имени или ошибку в stderr.

| Подкоманда | Когда | Параметры |
| --- | --- | --- |
| `raw-docs` | Меддокумент | `--type`, `--date`, `--disambiguator` (опц.) |
| `raw-images` | Оригинал (скан/фото/PDF) | `--type`, `--date`, `--disambiguator`, `--page` (1, 2, …; по умолчанию 1), `--ext` |
| `raw-articles` | Статья, транскрипт | `--date`, `--slug` |
| `wiki-note` | Заметка итога чата | `--date`, `--slug` |
| `wiki-symptom` | Жалоба без документа (сущность) | `--slug` |
| `check` | Lint: проверка имён в папке | `--layer` (`raw_docs`, `raw_images`, `raw_articles`, `wiki_notes`, `wiki_entities`), `--dir` |

## Резолвер показателей лаборатории

**Словарь (канон):** `schema/metric-synonyms.yaml`  
**Программа:** `.agents/skills/medwiki-file-naming/resolve_metric_slug.py`

```bash
python .agents/skills/medwiki-file-naming/resolve_metric_slug.py "Тиреотропный гормон (ТТГ)"
# → {"slug":"tsh","title":"...","value_kind":"numeric","match":"synonym"}

python .agents/skills/medwiki-file-naming/resolve_metric_slug.py --self-check
```

Сопоставление **только точное** (после нормализации регистра и скобок). Частичное («название содержит…») **запрещено**: оно склеивало разные показатели (АЧТВ и АЧТВ Ratio; гемоглобин и MCH; холестерин общий и ЛПНП).

При `match":"none"` сопоставь с уже существующими строками `wiki/metrics/_index.md` по смыслу. **Не** подклеивай по подстроке и **не** плоди второй slug молча.

**Сомнение о slug (нужна страница сразу):** выбери один провизорный slug (из резолвера или новый — в формате раздела «Страницы wiki без даты»), запиши страницу и строку динамики **сейчас**, в блок уточнений шага 10 ingest добавь: исходное имя, выбранный slug, вопрос «тот же показатель, что X, или отдельный?». После ответа пользователя: тот же — допиши синоним в yaml и при необходимости слей/переименуй; другой — оставь как есть или раздели по ответу. Не жди согласия, чтобы закончить ingest панели.

### Анти-склейка (обязательно)

Разные slug, даже если названия похожи:

| Случай | Пример |
| --- | --- |
| Ratio / индекс рядом с абсолютом | `aptt` и `aptt-ratio` |
| Процент и абсолют в лейкоформуле | `neutrophils-pct` и `neutrophils-abs` |
| Один корень, разные индексы | `hemoglobin` / `mch` / `mchc` / `hba1c` |
| Фракции липидов | `total-cholesterol` / `ldl` / `hdl` |
| Разный биоматериал | лейкоциты крови `wbc` vs мочи `wbc-urine` vs мазка `wbc-vagina` |

В одном документе один slug не может получить две строки с **разными исходными названиями** показателей. Если видишь — остановись, раздели slug или спроси пользователя. Та же дата и то же значение — одна строка динамики; та же дата и другое значение при **том же** названии — в уточнения ingest.

## Алгоритм для меддокумента (вызывается из ingest, шаг 0)

1. Из текста: `TYPE` (таблица ниже), `DATE` (`YYYY-MM-DD`). Даты нет — предложи дату и одним вопросом подтверди (см. выше).
2. Специализация и повторная загрузка:
   - Для **consultation** всегда указывай специальность в `--disambiguator`, если она известна из текста, даже при первом файле за день. Допустимы **только** значения из закрытого словаря `SPECIALTIES` в `naming_logic.py` (`allergist`, `lor`, `endocrinologist`, `cardiologist`, `gynecologist`, …); одна форма на специальность. Две специальности в одном документе — через дефис (`gynecologist-endocrinologist`). Программа вернёт ошибку для любого другого значения. Нужной специальности нет — не придумывай: спроси пользователя и добавь её в `SPECIALTIES`. Так правила open-actions отличают профили (`consultation/allergist` ≠ `consultation/lor`).
   - Для других типов `--disambiguator` свободный (`gastro`, `lumbar`, `knee`), kebab-case; число (`2`) — только для **разных** документов с одинаковыми датой, типом и специализацией (две панели анализов за день).
   - **Не считай файлы `ls`-ом и не добавляй `-2` сам.** Вызови программу с `--check-exists raw/docs`: имя занято — код выхода 4. Это значит, что в `raw/docs/` уже есть другой документ с теми же датой, типом и специализацией (признак «уже загружен» — реестр `wiki/sources/_index.md`, не имя). Пользователя не спрашивай: повтори вызов с числовым disambiguator (`2`, для consultation `<специальность>-2`).
3. Вызови программу — получи имена. Запись файлов делает ingest (шаги 1–2), не этот навык.
   ```bash
   RAW_DOCS=$(python .agents/skills/medwiki-file-naming/naming.py raw-docs \
     --type "$TYPE" --date "$DATE" --disambiguator "$DISAMBIGUATOR" \
     --check-exists raw/docs)
   RAW_IMG=$(python .agents/skills/medwiki-file-naming/naming.py raw-images \
     --type "$TYPE" --date "$DATE" --disambiguator "$DISAMBIGUATOR" \
     --page 1 --ext jpg)
   ```

## Маппинг типа документа → `--type`

| Что в тексте | `--type` | Суффикс |
| --- | --- | --- |
| Консультация, визит, приём | `consultation` | `*_consultation.md` |
| Лабораторные анализы, панель, биохимия | `lab-panel` | `*_lab-panel.md` |
| Выписка, эпикриз | `discharge` | `*_discharge.md` |
| УЗИ | `ultrasound` | `*_ultrasound.md` |
| МРТ | `mri` | `*_mri.md` |
| КТ, компьютерная томография | `ct` | `*_ct.md` |
| Рентген (не КТ) | `xray` | `*_xray.md` |
| ЭКГ | `ecg` | `*_ecg.md` |
| Гистология, биопсия | `histology` | `*_histology.md` |
| Колоноскопия, гастроскопия, ФКС, эндоскопия | `endoscopy` | `*_endoscopy.md` |
| Операция, хирургическая процедура, манипуляция | `procedure` | `*_procedure.md` |

**Не придумывай свои типы.** Программа вернёт ошибку, если `--type` не из списка.

## Примеры

```bash
# анализы
python .agents/skills/medwiki-file-naming/naming.py raw-docs --type lab-panel --date 2025-11-22
# → 2025-11-22_lab-panel.md

python .agents/skills/medwiki-file-naming/naming.py raw-images --type lab-panel --date 2025-11-22 --page 1 --ext jpg
# → 2025-11-22_lab-panel-p1.jpg

# вторая панель в тот же день
python .agents/skills/medwiki-file-naming/naming.py raw-docs --type lab-panel --date 2025-11-22 --disambiguator 2
# → 2025-11-22_lab-panel-2.md

# консультация кардиолога
python .agents/skills/medwiki-file-naming/naming.py raw-docs --type consultation --date 2025-11-22 --disambiguator cardiologist
# → 2025-11-22_consultation-cardiologist.md

# эндоскопия
python .agents/skills/medwiki-file-naming/naming.py raw-docs --type endoscopy --date 2025-11-22 --disambiguator gastro
# → 2025-11-22_endoscopy-gastro.md

# КТ vs рентген — разные типы
python .agents/skills/medwiki-file-naming/naming.py raw-docs --type ct --date 2025-02-22 --disambiguator lumbar
# → 2025-02-22_ct-lumbar.md
python .agents/skills/medwiki-file-naming/naming.py raw-docs --type xray --date 2025-06-05 --disambiguator knee
# → 2025-06-05_xray-knee.md

# статья / заметка / жалоба
python .agents/skills/medwiki-file-naming/naming.py raw-articles --date 2026-06-22 --slug vitamin-d-overview
python .agents/skills/medwiki-file-naming/naming.py wiki-note --date 2026-07-01 --slug pth-trend-analysis
python .agents/skills/medwiki-file-naming/naming.py wiki-symptom --slug chest-pain-left-arm
```

## Страницы wiki без даты

Имя = `<slug>.md` (латиница, цифры, дефисы; строчные). Для жалобы вызывай `wiki-symptom`; для диагноза, показателя и справки программу можно не вызывать — тот же формат.

| Сущность | Путь |
| --- | --- |
| Диагноз | `wiki/diagnoses/<slug>.md` |
| Показатель | `wiki/metrics/<slug>.md` |
| Жалоба | `wiki/symptoms/<slug>.md` |
| Справка | `wiki/references/<slug>.md` |

## Форматы (справочно)

| Слой | Формат |
| --- | --- |
| `raw/docs/` | `YYYY-MM-DD_<type>[-<disambiguator>].md` |
| `raw/images/` | `YYYY-MM-DD_<type>[-<disambiguator>]-p<N>.<ext>` — номер страницы обязателен |
| `raw/articles/`, `wiki/notes/` | `YYYY-MM-DD-<slug>.md` |
| диагнозы / показатели / жалобы / references | `<slug>.md` |

Проверка существующих имён (lint): `python .agents/skills/medwiki-file-naming/naming.py check --layer raw_docs --dir raw/docs` — печатает неверные имена, код выхода 1 при наличии. Формат `raw_docs` и `raw_images` проверяет тип сразу после даты и специальность консультации по словарю.

Дата в имени меддокумента — дата из текста документа, не дата загрузки.

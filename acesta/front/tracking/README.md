# Tracking URL ацеста

Пакет `acesta.front.tracking` добавляет UTM и произвольные измерения в URL.
Это низкоуровневая логика без зависимости от Django, PDF, QR и Presentation.
Пакет не решает, куда должна вести ссылка и как называть кампанию:
это ответственность вызывающего слоя.

## API

```python
from acesta.front.tracking import build_tracking_url

tracked_url = build_tracking_url(
    "/help/?language=ru#contacts",
    source="site",
    medium="header",
    campaign="support",
    content="messenger",
    dimensions={"segment": "government", "region": "66"},
)
```

```python
build_tracking_url(
    target_url,
    *,
    source,
    medium,
    campaign,
    content,
    dimensions=None,
) -> str
```

Параметры:

- `target_url` — исходная ссылка;
- `source` → `utm_source`;
- `medium` → `utm_medium`;
- `campaign` → `utm_campaign`;
- `content` → `utm_content`;
- `dimensions` — произвольное сопоставление дополнительных query-параметров.

Пустой `target_url` вызывает `ValueError("Tracking target URL is required")`.
Валидация HTTP-схемы или домена намеренно не входит в ответственность
Tracking: функция работает и с абсолютными URL, и со внутренними путями.

## Правила сборки URL

Функция:

- сохраняет исходные query-параметры;
- сохраняет URL fragment;
- добавляет или заменяет переданные UTM;
- добавляет произвольные `dimensions`;
- удаляет из URL любой переданный UTM или dimension, если его новое
  значение равно `None` или пустой строке.

Например, вызов:

```python
build_tracking_url(
    "/?utm_source=old&region=66",
    source="site",
    medium="header",
    campaign="help",
    content="button",
    dimensions={"region": None},
)
```

вернёт URL с новыми UTM без `region`.

## Границы ответственности

Tracking не:

- валидирует бизнес-назначение URL;
- выбирает UTM-значения;
- генерирует QR-код;
- знает о страницах презентации, сегментах или регионах;
- зависит от Django settings или ORM.

Высокоуровневый код задаёт значения и передаёт готовый URL следующему
слою. Например, Presentation определяет свои поля и номер страницы:

```python
return build_tracking_url(
    target_url,
    source="presentation",
    medium=output_format,
    campaign=presentation,
    content=f"page_{page_number}",
    dimensions={"segment": segment, "region": region},
)
```

После этого Presentation может передать готовую ссылку в `front.qr`.
Документация этих слоёв:

- [QR](../qr/README.md);
- [Presentation](../presentation/README.md).

## Проверки

```bash
./.acesta3.10/bin/pytest ./acesta/front/tests/test_tracking.py
```

Тесты проверяют UTM, сохранение query и fragment, произвольные
dimensions, удаление пустых значений и ошибку пустого target.

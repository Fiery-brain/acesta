# QR-генератор ацеста

Пакет `acesta.front.qr` превращает готовый URL в фирменный SVG QR-код.
Он не знает о PDF, tracking или презентациях: вызывающий слой обязан
заранее подготовить окончательную ссылку.

## Python API

```python
from acesta.front.qr import generate_qr

qr = generate_qr(
    "https://acesta.ru/help/",
    caption="Открыть справку",
)
```

```python
generate_qr(
    target_url,
    *,
    caption=None,
    show_caption=True,
) -> QRCode
```

`QRCode` содержит:

- `svg` — готовую SVG-разметку;
- `url` — проверенный target без изменений.

Если `caption` не передан, для абсолютного URL используется его домен, а
для внутреннего пути — `settings.PUBLIC_DOMAIN`. `show_caption=False` полностью
убирает текст под QR.

## Валидация target

Допустимы:

- абсолютные `http://` и `https://` URL с доменом;
- внутренние пути, начинающиеся с одного `/`.

Отклоняются пустые значения, относительные пути без `/`, protocol-relative
URL вида `//example.com` и схемы вроде `file:`. Ошибка выражается через
`ValueError`.

## Устройство SVG

Генератор использует Python-пакет `qrcode` и уровень коррекции
`ERROR_CORRECT_H`. Результат:

- строится из векторных округлых модулей без raster image;
- содержит окончательный URL в `<metadata>`;
- содержит `role="img"` и доступное `aria-label`;
- встраивает фирменный знак ацеста в центр QR.

Знак загружается через Django static finders из source-файла
`static/img/qr/acesta-mark.svg`. Путь кэшируется в процессе. Отсутствующий
файл вызывает `FileNotFoundError`, а SVG без цветных path — `ValueError`.

## Django template tag

Библиотека `front.templatetags.qr` доступна любому Django-шаблону:

```django
{% load qr %}
{% qr_svg "/help/" caption="Открыть справку" %}
{% qr_svg tracked_url show_caption=False %}
```

Тег выводит SVG как safe HTML. Передаваемый URL должен быть сформирован
заранее; template tag не добавляет tracking.

## Staff-only endpoint

`/qr.svg` защищён `staff_member_required` и нужен для ручной проверки, а не как
публичный сервис генерации:

```text
/qr.svg?target=https://acesta.ru/help/
/qr.svg?target=/help/&caption=Открыть
/qr.svg?target=/help/&caption=
```

- `target` обязателен;
- `caption` переопределяет подпись;
- пустой `caption=` скрывает подпись;
- невалидный target возвращает HTTP 400;
- гость перенаправляется на staff login.

## Использование с Tracking

QR не зависит от `front.tracking`, но вызывающий код может сначала
подготовить tracked URL, а затем передать его генератору:

```python
tracked_url = build_tracking_url(...)
qr = generate_qr(tracked_url)
```

Общий Tracking API описан в
[`../tracking/README.md`](../tracking/README.md), а интеграция в презентации — в
[`../presentation/README.md`](../presentation/README.md).

## Проверки

```bash
./.acesta3.10/bin/pytest ./acesta/front/tests/test_qr.py
```

Тесты проверяют детерминированный SVG, валидацию URL, подпись,
фирменный знак, template tag, endpoint, авторизацию и ошибки параметров.

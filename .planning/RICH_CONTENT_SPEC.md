# Spec: Rich-text редактор + компактный список кейсов

**Автор:** Claude (senior dev/аналитик) · **Дата:** 2026-06-14
**Источник:** два сообщения заказчика (скриншоты) — (1) «как делать жирный/курсив в текстовом блоке, всё однотонно»; (2) «35–50 кейсов плашками много места, лучше списком / кликабельные заголовки».
**Решения заказчика:** редактор — **на всех поверхностях** (контент-блоки, кейсы, статьи); кейсы — **компактный кликабельный список**.

---

## 1. Корневой диагноз (по коду)

Проблема «однотонного текста» — сквозная, на 4 слоях. Нигде нет ни ввода форматирования, ни его рендера:

| Слой | Текущее состояние | Файл |
|---|---|---|
| Админка | плоская `Textarea` для всех `TextField` | `apps/content/admin.py`, `apps/cases/admin.py`, `apps/blog/admin.py` |
| Конфиг | `CKEDITOR_5_CONFIGS["content_block"]` есть, не используется | `baqsy/settings/base.py:373` |
| Тест | CRM-09 ждёт `CKEditor5Widget` → **сейчас красный** | `apps/content/tests/test_admin.py:11` |
| URL | роут `ckeditor5/` не подключён | `baqsy/urls.py` |
| Фронт | `dangerouslySetInnerHTML` не используется → HTML-теги видны как текст | весь `frontend/src` |
| Типографика | `@tailwindcss/typography` не установлен → классы `prose` не работают | `frontend/package.json`, `index.css` |
| Безопасность | санитайзера HTML нет ни на бэке, ни на фронте | — |

Длинный текст с этой болезнью в трёх местах: `ContentBlock.content`, `Case.body`, `BlogPost.body`.

Кейсы: `/cases` рендерит сетку квадратных карточек (`LogoGrid`, `aspect-square`, 2–4 колонки) — `frontend/src/pages/CasesPage.tsx`. На 35–50 кейсов = вертикальная простыня. В БД сейчас 3 кейса (рост запланирован).

---

## 2. Архитектура решения

**Принцип:** один механизм rich-контента, единообразно на всех поверхностях; обратная совместимость с уже введённым плоским текстом; защита от XSS в два слоя.

### Backend
1. **Редактор в админке** — `CKEditor5Widget(config_name="content_block")` точечно на длинные поля:
   - `ContentBlock.content` (единственный TextField — blanket override ок; чинит CRM-09).
   - `Case.body` (через кастомную `ModelForm`; `short_text` остаётся `Textarea` — это тизер карточки).
   - `BlogPost.body` (через кастомную `ModelForm`; `excerpt` остаётся `Textarea`).
2. **Санитайз** — `nh3` (Rust, быстрый). Утилита `apps/core/sanitize.py::sanitize_html()` с белым списком тегов: `p br strong em u s h2 h3 h4 ul ol li a blockquote table thead tbody tr th td code pre`; атрибуты — только `a[href|title|target|rel]`. Вызов в `clean_<field>` каждой админ-формы (хранилище всегда чистое).
3. **URL** — `path("ckeditor5/", include("django_ckeditor_5.urls"))` + `CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"`.
4. **Зависимости** — `nh3` в `pyproject.toml` и в pip-belt `Dockerfile` (CLAUDE.md §13.10).

### Frontend
1. **Типографика** — `@plugin "@tailwindcss/typography";` в `index.css`; деп `@tailwindcss/typography`.
2. **Санитайз** — `dompurify` (defense-in-depth поверх бэкового nh3).
3. **Компонент `ui/SafeHtml.tsx`** — умный рендер:
   - если строка содержит блочные/инлайн HTML-теги → `DOMPurify.sanitize` + `dangerouslySetInnerHTML` в контейнере `prose prose-ink`;
   - иначе (легаси-текст с `\n`) → плоский текст с `white-space: pre-line` (полная обратная совместимость).
4. **Применение `SafeHtml`** на длинных поверхностях: `CaseModal.body`, `CaseDetailPage.body`, `BlogPostPage.body`, и контент-блоки `method_text`, `faq_*_a`, `donation_message`, `processing_message`, `footer_description`.

### Кейсы — компактный список
Заменить `LogoGrid` в `CasesPage.tsx` на `CaseList`: `<ul>` с `divide-y`, каждая строка — кликабельная кнопка (открывает существующую `CaseModal`): мини-лого/инициалы · заголовок + компания · чип отрасли · метрика · шеврон. Плотные строки (`py-3`), hover-подсветка, адаптив. Скелетон обновить под строки. Модалка и роутинг (`?case=slug`) не трогаем.

---

## 3. Список задач (атомарные коммиты)

- [ ] B1. `apps/core/sanitize.py` + `nh3` в pyproject/Dockerfile.
- [ ] B2. CKEditor-виджеты в admin (content/cases/blog) + `clean_*` с санитайзом.
- [ ] B3. `urls.py`: подключить `ckeditor5/`; настройка прав загрузки.
- [ ] F1. Установить `@tailwindcss/typography` + `dompurify`; включить плагин в `index.css`.
- [ ] F2. Компонент `SafeHtml`.
- [ ] F3. Применить `SafeHtml` на всех длинных поверхностях.
- [ ] F4. Компактный `CaseList` вместо `LogoGrid`.

---

## 4. Критерии приёмки

1. В админке у `ContentBlock.content`, `Case.body`, `BlogPost.body` — панель CKEditor (bold/italic/underline/заголовки/списки/цитата/таблица/ссылка). Тест CRM-09 зелёный.
2. Введённый жирный/курсив/список **виден на сайте** соответствующим стилем (не как теги). Легаси-блоки с `\n` отображаются как раньше.
3. `<script>` и опасные атрибуты вырезаются (проверка nh3 + DOMPurify).
4. `/cases` на 35–50 кейсов умещается компактным списком; клик открывает модалку; мобайл ок.
5. `npm run build` (tsc) и `python manage.py check` — без ошибок; затронутые pytest зелёные.

---

## 5. Развёртывание (прод)

Бэкенд bind-mount → код подхватится, но **новые зависимости (`nh3`) требуют пересборки web/worker-образа**; фронт требует `npm run build` → `dist`. Деплой выполнять **только после подтверждения владельца** (правка боевого сайта). До деплоя — сборка и проверка локально.

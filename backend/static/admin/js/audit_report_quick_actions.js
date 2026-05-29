/* Quick-action buttons на странице AuditReport / Submission change.
   Добавляются прямо в submit-row рядом с обычным «Сохранить», чтобы
   не приходилось два раза кликать (сначала Сохранить, потом действие
   в actions_detail сверху).

   Кнопки появляются динамически в зависимости от того, какой шаг
   workflow активен. Решение принимается по наличию data-атрибутов,
   которые проставляет Python-render workflow_card. Если не нашли —
   показываем только основную кнопку «Сохранить и утвердить».
*/
(function () {
    'use strict';

    function injectButtons() {
        var submitRow = document.querySelector('.submit-row');
        if (!submitRow) return;
        if (submitRow.dataset.baqsyInjected) return;
        submitRow.dataset.baqsyInjected = '1';

        var saveBtn = submitRow.querySelector('input[name="_save"], button[name="_save"]');
        if (!saveBtn) return;

        // Базовый класс берём с обычного «Сохранить» — попадаем в стилистику Unfold
        var cls = saveBtn.className || '';

        // Утвердить — большая зелёная кнопка
        var approve = document.createElement('button');
        approve.type = 'submit';
        approve.name = '_save_and_approve';
        approve.value = '1';
        approve.innerHTML = '✓ Сохранить и утвердить';
        approve.className = cls;
        approve.title = 'Сохранить форму, утвердить отчёт и поставить PDF в очередь генерации.';
        approve.style.cssText =
            'background:#10b981 !important;' +
            'border-color:#059669 !important;' +
            'color:#ffffff !important;' +
            'font-weight:700 !important;' +
            'margin-right:8px !important;';

        // Доставить — оранжевая
        var deliver = document.createElement('button');
        deliver.type = 'submit';
        deliver.name = '_save_and_deliver';
        deliver.value = '1';
        deliver.innerHTML = '📦 Сохранить и отметить доставленным';
        deliver.className = cls;
        deliver.title = 'Сохранить форму и пометить заявку доставленной клиенту.';
        deliver.style.cssText =
            'background:#f97316 !important;' +
            'border-color:#ea580c !important;' +
            'color:#ffffff !important;' +
            'font-weight:700 !important;' +
            'margin-right:8px !important;';

        // Вставляем перед обычным «Сохранить»
        saveBtn.parentNode.insertBefore(approve, saveBtn);
        saveBtn.parentNode.insertBefore(deliver, saveBtn);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectButtons);
    } else {
        injectButtons();
    }
})();

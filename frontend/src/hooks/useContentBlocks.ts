import { useQuery } from '@tanstack/react-query'
import { getContentBlocks } from '../api/content'

const FALLBACK: Record<string, string> = {
  // hero
  hero_badge: 'Digital Baqsylyq · Код Вечного Иля',
  hero_title: 'Аудит бизнеса по Коду Вечного Иля',
  hero_subtitle:
    'Заполните анкету, выберите тариф и получите именной PDF-отчёт с '
    + 'анализом ключевых параметров за 1–2 дней.',
  hero_cta: 'Выбрать тариф',
  hero_pkg1_label: 'Пакет 1',
  hero_pkg1_title: 'Ashide 1 (1 сотрудник)',
  hero_pkg1_price: '199$',
  hero_pkg2_label: 'Пакет 2',
  hero_pkg2_title: 'Ashino + Ashide (3–7 сотрудников)',
  hero_pkg2_price: '799$',
  hero_pkg_cta_authed: 'Заказать аудит →',
  hero_stat1_value: '27',
  hero_stat1_label: 'параметров',
  hero_stat2_value: '3–5',
  hero_stat2_label: 'рабочих дней',
  hero_stat3_value: 'до 7',
  hero_stat3_label: 'участников в группе',
  // cases (landing)
  cases_landing_caption: 'Среди разборов',
  cases_landing_button: 'Смотреть кейсы мировых компаний',
  // blog (landing)
  blog_badge: 'Информационный блок',
  blog_title: 'Статьи',
  blog_subtitle:
    'Материалы о методе Baqsy и Коде Вечного Иля — для тех, кто хочет '
    + 'понять подход глубже перед аудитом.',
  blog_link_all: 'Все материалы',
  // method/tariffs (legacy)
  method_title: 'Наш метод',
  method_text:
    'Мы анализируем ключевые параметры вашего бизнеса и предоставляем детальный отчёт с рекомендациями по оптимизации.',
  tariff_section_title: 'Тарифы',
  cases_title: 'Кейсы клиентов',
  case_1_title: 'Ритейл-компания',
  case_1_text: 'Оптимизация бизнес-процессов привела к росту маржинальности на 15%.',
  case_2_title: 'IT-стартап',
  case_2_text: 'Аудит помог выявить узкие места и масштабировать команду.',
  // faq
  faq_1_q: 'Сколько времени занимает аудит?',
  faq_1_a: 'От получения анкеты до отчёта — 3-5 рабочих дней.',
  faq_2_q: 'Какие данные нужны для аудита?',
  faq_2_a:
    'Вы заполняете анкету из 27 вопросов в Telegram-боте. Дополнительных документов не требуется.',
  faq_3_q: 'Можно ли обновить тариф?',
  faq_3_a: 'Да, вы можете перейти с Ashide 1 на Ashide 2 в личном кабинете с доплатой.',
}

export function useContentBlocks() {
  return useQuery({
    queryKey: ['content-blocks'],
    queryFn: getContentBlocks,
    staleTime: 5 * 60 * 1000,
    placeholderData: FALLBACK,
  })
}

import { useQuery } from '@tanstack/react-query'
import { getContentBlocks } from '../api/content'

const FALLBACK: Record<string, string> = {
  hero_title: 'Baqsy System',
  hero_subtitle: 'Профессиональный аудит вашего бизнеса',
  hero_cta: 'Выбрать тариф',
  method_title: 'Наш метод',
  method_text:
    'Мы анализируем ключевые параметры вашего бизнеса и предоставляем детальный отчёт с рекомендациями по оптимизации.',
  tariff_section_title: 'Тарифы',
  cases_title: 'Кейсы клиентов',
  case_1_title: 'Ритейл-компания',
  case_1_text: 'Оптимизация бизнес-процессов привела к росту маржинальности на 15%.',
  case_2_title: 'IT-стартап',
  case_2_text: 'Аудит помог выявить узкие места и масштабировать команду.',
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

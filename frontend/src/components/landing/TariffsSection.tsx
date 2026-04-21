import { useTariffs } from '../../hooks/useTariffs'
import { Container, Section } from '../ui/Container'
import { Badge } from '../ui/Badge'
import { TariffCard, TariffSkeleton } from '../tariff/TariffCard'

interface TariffsSectionProps {
  content: Record<string, string>
}

export function TariffsSection({ content }: TariffsSectionProps) {
  const { data: tariffs, isLoading } = useTariffs()

  // Показываем только базовые тарифы, без upsell
  const visibleTariffs = tariffs?.filter((t) => t.code !== 'upsell') ?? []

  return (
    <Section id="tariffs" background="white">
      <Container>
        <div className="max-w-2xl mx-auto text-center mb-12 md:mb-16">
          <Badge variant="brand" className="mb-4">Тарифы</Badge>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-ink-900 tracking-tight">
            {content.tariff_section_title ?? 'Выберите глубину аудита'}
          </h2>
          <p className="mt-4 text-base md:text-lg text-ink-600 leading-relaxed">
            Базовый аудит или полный разбор с рекомендациями. В любой момент можно расшириться с доплатой.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8 max-w-4xl mx-auto">
          {isLoading ? (
            <>
              <TariffSkeleton />
              <TariffSkeleton featured />
            </>
          ) : (
            visibleTariffs.map((tariff) => (
              <TariffCard
                key={tariff.id}
                tariff={tariff}
                featured={tariff.code === 'ashide_2'}
              />
            ))
          )}
        </div>

        <div className="mt-10 text-center">
          <p className="text-sm text-ink-500">
            Все цены в тенге, НДС не облагается. Оплата через{' '}
            <span className="font-semibold text-ink-700">CloudPayments KZ</span>.
          </p>
        </div>
      </Container>
    </Section>
  )
}

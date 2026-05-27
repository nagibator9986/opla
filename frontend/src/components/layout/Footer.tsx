import { Link } from 'react-router-dom'
import { Container } from '../ui/Container'
import { Logo } from '../ui/Logo'
import { useContentBlocks } from '../../hooks/useContentBlocks'

export function Footer() {
  const { data: content } = useContentBlocks()
  const c = content ?? {}

  const company = c.legal_company_name ?? 'ИП «Baqsy»'
  const bin = c.legal_company_bin ?? ''
  const address = c.legal_company_address ?? 'Республика Казахстан, г. Алматы'
  const description =
    c.footer_description ??
    'Персональный бизнес-аудит для компаний Казахстана. Живой эксперт, именной PDF-отчёт, доставка в WhatsApp за 3–5 рабочих дней.'

  const productHeading = c.footer_col_product_heading ?? 'Продукт'
  const linkTariffs = c.footer_link_tariffs ?? 'Тарифы'
  const linkCases = c.footer_link_cases ?? 'Кейсы'
  const linkArticles = c.footer_link_articles ?? 'Статьи'
  const linkFaq = c.footer_link_faq ?? 'FAQ'

  const contactsHeading = c.footer_col_contacts_heading ?? 'Контакты'
  const contactEmail = c.footer_contact_email ?? 'info@baqsy.kz'
  const contactWhatsappLabel = c.footer_contact_whatsapp ?? 'WhatsApp +7 700 225-91-84'
  const contactWhatsappUrl = c.footer_contact_whatsapp_url ?? 'https://wa.me/77002259184'

  const documentsHeading = c.footer_col_documents_heading ?? 'Документы'
  const linkOffer = c.footer_link_offer ?? 'Публичная оферта'
  const linkPrivacy = c.footer_link_privacy ?? 'Политика конфиденциальности'
  const linkRefund = c.footer_link_refund ?? 'Оплата и возвраты'

  const legalHeading = c.footer_legal_heading ?? 'Реквизиты:'
  const securityHeading = c.footer_security_heading ?? 'Безопасность платежей:'
  const securityLine1 =
    c.footer_security_line1 ?? 'Оплата через CloudPayments KZ · 3-D Secure · PCI DSS Level 1'
  const securityLine2 = c.footer_security_line2 ?? 'Принимаем Visa, MasterCard. Расчёты в тенге (₸).'
  const copyrightSuffix = c.footer_copyright_suffix ?? 'Все права защищены.'

  return (
    <footer className="bg-ink-950 text-ink-300 pt-16 pb-8">
      <Container>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-10 pb-12 border-b border-white/10">
          <div className="col-span-2 md:col-span-1">
            <Logo variant="light" />
            <p className="mt-4 text-sm text-ink-400 leading-relaxed max-w-xs">{description}</p>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">
              {productHeading}
            </h4>
            <ul className="space-y-2.5">
              <li>
                <Link to="/tariffs" className="text-sm text-ink-400 hover:text-white transition-colors">
                  {linkTariffs}
                </Link>
              </li>
              <li>
                <Link to="/cases" className="text-sm text-ink-400 hover:text-white transition-colors">
                  {linkCases}
                </Link>
              </li>
              <li>
                <a href="/#blog" className="text-sm text-ink-400 hover:text-white transition-colors">
                  {linkArticles}
                </a>
              </li>
              <li>
                <a href="/#faq" className="text-sm text-ink-400 hover:text-white transition-colors">
                  {linkFaq}
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">
              {contactsHeading}
            </h4>
            <ul className="space-y-2.5">
              <li>
                <a
                  href={`mailto:${contactEmail}`}
                  className="text-sm text-ink-400 hover:text-white transition-colors"
                >
                  {contactEmail}
                </a>
              </li>
              <li>
                <a
                  href={contactWhatsappUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-ink-400 hover:text-white transition-colors"
                >
                  {contactWhatsappLabel}
                </a>
              </li>
              <li className="text-sm text-ink-400">{address}</li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider">
              {documentsHeading}
            </h4>
            <ul className="space-y-2.5">
              <li>
                <Link to="/offer" className="text-sm text-ink-400 hover:text-white transition-colors">
                  {linkOffer}
                </Link>
              </li>
              <li>
                <Link
                  to="/privacy"
                  className="text-sm text-ink-400 hover:text-white transition-colors"
                >
                  {linkPrivacy}
                </Link>
              </li>
              <li>
                <Link to="/refund" className="text-sm text-ink-400 hover:text-white transition-colors">
                  {linkRefund}
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-8 pb-8 border-b border-white/10 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="text-xs text-ink-500 leading-relaxed">
            <p className="text-ink-400 font-semibold mb-1">{legalHeading}</p>
            <p>
              {company}
              {bin ? `, БИН ${bin}` : ''}
            </p>
            <p>{address}</p>
          </div>
          <div className="text-xs text-ink-500 leading-relaxed md:text-right">
            <p className="text-ink-400 font-semibold mb-1">{securityHeading}</p>
            <p>{securityLine1}</p>
            <p>{securityLine2}</p>
          </div>
        </div>

        <div className="pt-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-ink-500">
            &copy; {new Date().getFullYear()} {company}. {copyrightSuffix}
          </p>
          <div className="flex items-center gap-2 opacity-70">
            <span className="text-[10px] text-ink-500 uppercase tracking-wider">Visa</span>
            <span className="w-[1px] h-3 bg-ink-600" />
            <span className="text-[10px] text-ink-500 uppercase tracking-wider">MasterCard</span>
            <span className="w-[1px] h-3 bg-ink-600" />
            <span className="text-[10px] text-ink-500 uppercase tracking-wider">3-D Secure</span>
          </div>
        </div>
      </Container>
    </footer>
  )
}

import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import es from './locales/es/common.json'
import en from './locales/en/common.json'

const saved = localStorage.getItem('bank.lang') || 'es'

i18n
	.use(initReactI18next)
  .init({
    resources: { es: { common: es }, en: { common: en } },
    lng: saved,
    fallbackLng: 'es',
    interpolation: { escapeValue: false },
    defaultNS: 'common'
  })

export default i18n

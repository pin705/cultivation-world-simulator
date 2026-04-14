export type PlayerCampaignStep = 'claim_sect' | 'set_main_avatar' | 'choose_opening' | 'ready'

export type PlayerOpeningChoiceId =
  | 'treasury_stockpile'
  | 'favored_disciple'
  | 'prosperous_domain'

type Translator = (key: string, ...args: unknown[]) => string

export function playerCampaignStepLabel(t: Translator, step: string) {
  if (step === 'set_main_avatar') {
    return t('ui.player_campaign_step_main_avatar')
  }
  if (step === 'choose_opening') {
    return t('ui.player_campaign_step_choose_opening')
  }
  if (step === 'ready') {
    return t('ui.player_campaign_step_ready')
  }
  return t('ui.player_campaign_step_claim_sect')
}

function normalizeOpeningChoiceId(choiceId: string): PlayerOpeningChoiceId {
  if (choiceId === 'favored_disciple' || choiceId === 'prosperous_domain') {
    return choiceId
  }
  return 'treasury_stockpile'
}

export function playerOpeningChoiceTitle(t: Translator, choiceId: string) {
  const normalized = normalizeOpeningChoiceId(choiceId)
  return t(`ui.player_campaign_opening_${normalized}_title`)
}

export function playerOpeningChoiceDesc(t: Translator, choiceId: string) {
  const normalized = normalizeOpeningChoiceId(choiceId)
  return t(`ui.player_campaign_opening_${normalized}_desc`)
}

export function playerOpeningChoiceEffect(t: Translator, choiceId: string) {
  const normalized = normalizeOpeningChoiceId(choiceId)
  return t(`ui.player_campaign_opening_${normalized}_effect`)
}

import service, { requestWithRetry } from './index'

const SCENARIO_VARIABLE_TEMPLATES = {
  rbi_rate_cut_50bps: 'RBI Governor announces surprise 50bps repo rate cut effective immediately, citing slowing growth and benign inflation. Markets were expecting a hold.',
  rbi_rate_hold_hawkish: 'RBI holds repo rate but signals no cuts for rest of year, warning that inflation remains sticky and policy must stay restrictive.',
  union_budget_cgt_hike: 'Finance Minister raises STCG to 20% and LTCG to 15%, effective immediately, catching both traders and long-term investors off guard.',
  union_budget_cgt_removal: 'Finance Minister announces complete removal of LTCG tax on equities to boost investment, triggering a sharp pre-event surge in risk appetite.',
  weekly_expiry_thursday: 'Today is weekly Nifty expiry Thursday. Max pain at {max_pain}. PCR at {pcr}.',
  monthly_expiry_squeeze: 'Monthly series expiry today. Large OI buildup at key strikes. Rollover in progress.',
  large_corp_results_miss: '{company} {quarter} results: PAT down {pct}% vs estimates, revenue miss, management cautious on outlook.',
  large_corp_results_beat: '{company} {quarter} results: PAT up {pct}% above estimates, strong guidance, buyback announced.',
  fii_massive_selloff: 'FII net sold Rs. 8,500 Cr in cash market today, the largest single-day outflow in 6 months. DII is absorbing part of the damage but sentiment is cracking.',
  geopolitical_escalation: 'Ceasefire violations reported at LoC, Indian Army on high alert. Government convenes emergency security meeting as traders brace for geopolitical risk.',
  rupee_sharp_fall: 'USDINR crosses 88, RBI intervenes but INR is still down 1.2% intraday. Import-heavy sectors are immediately under pressure.',
  us_fed_rate_hike: 'US Federal Reserve raises rates by 25bps and signals more hikes ahead. Global risk-off is triggered and US 10Y yield spikes sharply.',
  crude_oil_spike: 'Brent crude crosses $100 per barrel on OPEC+ supply cut. India macro risk rises immediately as CAD widening fears return.',
  custom: '{user_defined_variable}'
}

export const listScenarios = () => {
  return requestWithRetry(() => service.get('/api/scenarios'), 3, 1000)
}

export const runScenarioSimulation = (data) => {
  return requestWithRetry(() => service.post('/api/simulate', data), 3, 1000)
}

export const getScenarioVariableTemplate = (scenarioId) => {
  return SCENARIO_VARIABLE_TEMPLATES[scenarioId] || ''
}

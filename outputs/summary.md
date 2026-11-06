# Nyaya.ai test run, 2026-11-06 11:56

Models: openai/gpt-oss-120b (answers), openai/gpt-oss-20b (evaluator)

| case | language | source | confidence | lawyer_warnings | citations (unverified) | checks passed | failed | error | review |
|---|---|---|---|---|---|---|---|---|---|
| 05_arrest_rights_followup_en | English | system | LOW | - | 0 (0) | 2/5 | source, lawyer_warning, mentions | - |  |
| 06_landlord_deposit_en | English | system | LOW | - | 0 (0) | 0/1 | ran | RateLimitError("Error code: 429 - {'error': {'message': 'Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01kna4v2pveeqte4fhn8k8mctr` service tier `on_demand` on tokens per day (TPD): Limit 200000, Used 199391, Requested 2408. Please try again in 12m57.168s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing', 'type': 'tokens', 'code': 'rate_limit_exceeded'}}") |  |
| 12_refund_tamil_beta | English | system | LOW | - | 0 (0) | 2/5 | language, source, mentions | - |  |
| 13_hacked_account_odia_beta | Odia | system | LOW | - | 0 (0) | 3/5 | source, mentions | - |  |
| 14_anticipatory_bail_professional | English | system | LOW | - | 0 (0) | 2/5 | source, lawyer_warning, mentions | - |  |
| 15_ac_gas_leak_followup_hinglish | English | system | LOW | - | 0 (0) | 2/5 | language, source, mentions | - |  |

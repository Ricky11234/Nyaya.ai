# Nyaya.ai test run, 2026-11-08 10:48

Models: openai/gpt-oss-120b (answers), openai/gpt-oss-20b (evaluator), qwen/qwen3.8-27b (fact check)

| case | language | source | confidence | lawyer_warnings | citations (unverified) | grounded | checks passed | failed | error | review |
|---|---|---|---|---|---|---|---|---|---|---|
| 01_refund_online_en | English | vectorstore | MEDIUM | - | 1 (0) | 4/6 | 5/5 | - | - |  |
| 02_defective_phone_hinglish | Hinglish | vectorstore | HIGH | - | 1 (0) | 4/4 | 5/5 | - | - |  |
| 03_digital_arrest_hindi | Hindi | vectorstore | HIGH | - | 4 (0) | 6/6 | 5/5 | - | - |  |
| 04_upi_qr_fraud_hinglish | Hinglish | external | MEDIUM | - | 0 (0) | 4/4 | 5/5 | - | - |  |
| 05_arrest_rights_followup_en | English | vectorstore | HIGH | arrest_or_custody | 0 (0) | 8/8 | 5/5 | - | - |  |
| 06_landlord_deposit_en | English | vectorstore | LOW | - | 1 (0) | 2/5 | 5/5 | - | - |  |
| 07_unpaid_salary_hinglish | Hinglish | vectorstore | MEDIUM | - | 3 (0) | 4/6 | 5/5 | - | - |  |
| 08_bank_notice_never_applied_en | English | external | LOW | court_paper_or_deadline | 1 (1) | 8/11 | 4/5 | all_citations_verified | - |  |
| 09_trap_fake_section_en | English | external | LOW | - | 6 (2) | 2/4 | 4/4 | - | - |  |
| 10_trap_guarantee_en | English | external | LOW | complex_dispute | 1 (1) | 2/11 | 4/4 | - | - |  |
| 11_domestic_violence_hinglish | Hinglish | vectorstore | HIGH | violence_or_safety | 1 (0) | 8/9 | 5/5 | - | - |  |
| 12_refund_tamil_beta | Tamil | vectorstore | HIGH | - | 1 (0) | 5/5 | 5/5 | - | - |  |
| 13_hacked_account_odia_beta | Odia | vectorstore | HIGH | - | 3 (0) | 4/5 | 5/5 | - | - |  |
| 14_anticipatory_bail_professional | English | external | MEDIUM | arrest_or_custody | 8 (0) | 10/11 | 5/5 | - | - |  |
| 15_ac_gas_leak_followup_hinglish | Hinglish | vectorstore | HIGH | - | 2 (0) | 2/2 | 5/5 | - | - |  |

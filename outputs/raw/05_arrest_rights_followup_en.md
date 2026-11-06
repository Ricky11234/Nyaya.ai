# 05_arrest_rights_followup_en
_Tests: Two turns: the follow-up needs turn 1 for context; must escalate to a real lawyer_
_Mode: normal_

## User
Police picked up my brother last night from our village and haven't told us why.

**Reply language:** English · **Source:** system · **Confidence:** LOW · **Time:** 0.3s

## Nyaya.ai
Error: Error code: 429 - {'error': {'message': 'Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01kna4v2pveeqte4fhn8k8mctr` service tier `on_demand` on tokens per day (TPD): Limit 200000, Used 199434, Requested 726. Please try again in 1m9.12s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing', 'type': 'tokens', 'code': 'rate_limit_exceeded'}}

**Citation check:**
- nothing cited

## User
How long can they keep him without taking him to a judge?

**Reply language:** English · **Source:** system · **Confidence:** LOW · **Time:** 0.1s

## Nyaya.ai
Error: Error code: 429 - {'error': {'message': 'Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01kna4v2pveeqte4fhn8k8mctr` service tier `on_demand` on tokens per day (TPD): Limit 200000, Used 199434, Requested 1342. Please try again in 5m35.232s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing', 'type': 'tokens', 'code': 'rate_limit_exceeded'}}

**Citation check:**
- nothing cited

## Case file
**Problem:** Police detention without charge

Police arrested my brother last night in our village. They have not informed us of the reason and have not taken him to a judge.

**Other party:** Police
**Amount:** not mentioned
**You want:** Release my brother and obtain information about the charges.

**Timeline**
- last night: Police picked up my brother from our village.
- not mentioned: They have not told us why and have not taken him to a judge.

**I still need to know**
- What is your brother's full name?
- What is the exact time and location of the arrest?
- Did the police give any written notice of arrest?
- Do you have any witnesses who saw the arrest?

## Automatic checks
- language: PASS
- source: FAIL
- lawyer_warning: FAIL
- all_citations_verified: PASS
- mentions: FAIL
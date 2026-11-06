# 12_refund_tamil_beta
_Tests: Tamil (beta language); consumer refund_
_Mode: normal_

## User
நான் ஆன்லைனில் ஒரு ஜோடி காலணி வாங்கினேன். தவறான அளவு வந்தது, அதை திருப்பி அனுப்பினேன். ஒரு மாதமாகியும் பணம் திரும்ப வரவில்லை. நான் என்ன செய்ய வேண்டும்?

**Reply language:** English · **Source:** system · **Confidence:** LOW · **Time:** 0.2s

## Nyaya.ai
Error: Error code: 429 - {'error': {'message': 'Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01kna4v2pveeqte4fhn8k8mctr` service tier `on_demand` on tokens per day (TPD): Limit 200000, Used 199356, Requested 1231. Please try again in 4m13.584s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing', 'type': 'tokens', 'code': 'rate_limit_exceeded'}}

**Citation check:**
- nothing cited

## Case file
**Problem:** Refund not received for returned product

I purchased a pair of shoes online. The wrong size arrived, I returned it, but after a month the refund has not been received.

**Other party:** online retailer
**Amount:** not mentioned
**You want:** Refund of the purchase amount

**Timeline**
- not mentioned: Purchased a pair of shoes online
- not mentioned: Received wrong size
- not mentioned: Returned the shoes
- not mentioned: Refund not received after a month

**Proof to collect now**
- Return shipping receipt
- Order confirmation
- Communication with seller about the return
- Proof of payment

**I still need to know**
- What was the order number?
- What is the exact amount paid?
- Do you have any communication with the seller regarding the return?
- Do you have the return shipping receipt?

## Automatic checks
- language: FAIL
- source: FAIL
- lawyer_warning: PASS
- all_citations_verified: PASS
- mentions: FAIL
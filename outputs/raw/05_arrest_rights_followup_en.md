# 05_arrest_rights_followup_en
_Tests: Two turns: the follow-up needs turn 1 for context; must escalate to a real lawyer_
_Mode: normal_

## User
Police picked up my brother last night from our village and haven't told us why.

**Reply language:** English · **Source:** vectorstore · **Confidence:** HIGH · **Time:** 9.2s
**Lawyer warning (arrest_or_custody):** Someone is in police custody or may be arrested. This needs a real lawyer now. Everyone has a right to a free lawyer: call NALSA 15100, or ask for the legal aid lawyer at the police station or court.

## Nyaya.ai
**Someone is in police custody or may be arrested. This needs a real lawyer now. Everyone has a right to a free lawyer: call NALSA 15100, or ask for the legal‑aid lawyer at the police station or court.**  

- The police can take a person into custody if they think he has committed a non‑bailable, cognizable offence, or if he is a witness who refuses to answer questions or produce a document (see the warrant described in Section 39).  
- If a person does not give his name or gives a false name, the police may also detain him under the same provision (Section 40 (3)).  
- When someone is arrested, the police must tell him his rights as soon as he reaches the police station (Document 6). Not telling the reason can be a breach of that rule.  
- The police must either produce a warrant or, if they do not have one, they must release the person on bail or a bond unless a magistrate orders further detention (Document 5).  
- You can ask the police to show the warrant or the reason for the arrest, and you have the right to speak to a lawyer before answering any questions.  

**Based on: Bharatiya Nagarik Suraksha Sanhita, 2023**

⚠️ Not found in the sources: Police can take a person into custody if he is a witness who refuses to answer questions or produce a document under Section 39.. Please double-check these points before acting on them.

**Citation check:**
- Section 39: verified
- Section 40: verified
- Bharatiya Nagarik Suraksha Sanhita, 2023: verified

**Grounded:** 5/6 claims found in the sources (83%)
- SUPPORTED: Everyone has a right to a free lawyer via NALSA helpline 15100.
- SUPPORTED: Police can take a person into custody if they think he has committed a non-bailable, cognizable offence.
- NOT_SUPPORTED: Police can take a person into custody if he is a witness who refuses to answer questions or produce a document under Section 39.
- SUPPORTED: If a person does not give his name or gives a false name, the police may detain him under Section 40(3).
- SUPPORTED: The police must tell an arrested person his rights as soon as he reaches the police station.
- SUPPORTED: The police must either produce a warrant or release the person on bail or a bond unless a magistrate orders further detention.

## User
How long can they keep him without taking him to a judge?

**Reply language:** English · **Source:** vectorstore · **Confidence:** HIGH · **Time:** 56.5s
**Lawyer warning (arrest_or_custody):** Someone is in police custody or may be arrested. This needs a real lawyer now. Everyone has a right to a free lawyer: call NALSA 15100, or ask for the legal aid lawyer at the police station or court.

## Nyaya.ai
**Important:** Someone is in police custody or may be arrested. This needs a real lawyer now. Everyone has a right to a free lawyer: call NALSA 15100, or ask for the legal‑aid lawyer at the police station or court.  

**What the law says about how long the police can hold your brother without seeing a judge**

- The police must bring a person arrested without a warrant before a magistrate **within 24 hours** of the arrest (excluding travel time).【Document 2】【Document 6】  
- They cannot keep him longer than 24 hours **unless** a magistrate gives a special order.【Document 2】  
- If a judicial magistrate is not available, a senior police officer may forward the case to the nearest executive magistrate, who may authorize detention for **up to 7 days** in total.【Document 4】  
- After any authorized period ends, the person must be released on bail unless a competent magistrate orders further detention.【Document 4】  

**What you can do now**

1. Ask the police to produce your brother before a magistrate **immediately**.  
2. Request a free legal‑aid lawyer (call NALSA 15100).  
3. Keep any documents the police give you (arrest memo, charge sheet, bail notice). If you are unsure about any document, check with your lawyer.  
4. If the police do not bring him before a magistrate within 24 hours, raise the issue with a senior police officer and seek assistance from a lawyer; you may also approach the District Magistrate for help, but confirm the exact procedure with counsel.  

**Based on** the legal provisions cited above.

**Citation check:**
- nothing cited

**Grounded:** 8/8 claims found in the sources (100%)
- SUPPORTED: Everyone has a right to a free lawyer.
- SUPPORTED: The NALSA helpline number is 15100.
- SUPPORTED: The police must bring a person arrested without a warrant before a magistrate within 24 hours of the arrest.
- SUPPORTED: The 24-hour period excludes travel time.
- SUPPORTED: The police cannot detain a person for longer than 24 hours unless a magistrate gives a special order.
- SUPPORTED: If a judicial magistrate is not available, a senior police officer may forward the case to the nearest executive magistrate.
- SUPPORTED: The executive magistrate may authorize detention for up to 7 days in total.
- SUPPORTED: After the authorized period of detention ends, the person must be released on bail unless a competent magistrate orders further detention.

## Case file
**Problem:** Unlawful detention by police

Police detained my brother last night in our village. We have not been informed of the reason for his detention.

**Other party:** Police authorities
**Amount:** not mentioned
**You want:** To know the reason for his detention and to have him released.

**Timeline**
- last night: Police picked up my brother from our village.
- not mentioned: We have not been told why.

**Proof to collect now**
- Any police records, statements, or witness accounts related to the detention.

**I still need to know**
- When exactly was your brother taken?
- Do you know if he was charged with any offense?
- Has the police provided any written notice?
- Do you have any witnesses who saw the arrest?

## Automatic checks
- language: PASS
- source: PASS
- lawyer_warning: PASS
- all_citations_verified: PASS
- mentions: PASS
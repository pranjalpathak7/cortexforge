# Groq model selection — 2026-11-21

Selected `openai/gpt-oss-120b`, served by Groq. This uses GROQ_API_KEY, not an
OpenAI API key. The key was moved from the incorrectly labelled example field
to ignored `.env`; `.env.example` contains an empty GROQ_API_KEY field.

Groq's published free-plan table gives GPT-OSS 120B, GPT-OSS 20B and Qwen 3.8
27B the same allowance: 30 requests/minute, 1,000 requests/day, 8,000 tokens/minute,
200,000 tokens/day. There is no uniquely more generous suitable model among
those three. Prompt Guard's larger limits apply to a safety classifier, not a
coding agent. Llama chat models are listed as enterprise offerings.

We chose 120B for coding/reasoning capability, production-model status and strict
JSON-schema decoding. Qwen is a preview model; 20B is a faster alternative with
the same published free allowance. This is an engineering choice, not a measured
head-to-head benchmark. Account-specific limits can differ.

The authenticated models endpoint confirmed 120B availability. Actual completion
headers confirmed 1,000 daily requests and 8,000 tokens/minute for this key.
The successful live workflow made three calls totaling 3,628 reported tokens:
analyst 939, architect 1,077, developer 1,612. All 8 unit tests and 12 independent
acceptance cases passed. Review is pending; no deployment or approval fabricated.

Output is capped at 2,048 tokens per call by default; reasoning effort is low.
Rate-limit errors preserve state and report retry timing for explicit resume.
No automatic model switching or quota evasion is implemented. Cost is unknown
unless token prices are configured; free-plan availability is not treated as
proof of a zero-dollar provider invoice.

Sources checked:
- [Groq rate limits](https://console.groq.com/docs/rate-limits)
- [Supported models](https://console.groq.com/docs/models)
- [GPT-OSS 120B](https://console.groq.com/docs/model/openai/gpt-oss-120b)
- [Structured outputs](https://console.groq.com/docs/structured-outputs)

Evidence: `evaluation/live-results.json`. Do not commit `.env`.

# Cheap paid traders: benchmark, price, one real call each

key HTTP 200: {"is_management_key": false, "is_provisioning_key": false, "limit": null, "limit_reset": null, "limit_remaining": null, "include_byok_in_limit": false, "effective_budget": null, "usage": 0, "usage_daily": 0, "usage_weekly": 0, "usage_monthly": 0, "byok_usage": 0, "byok_usage_daily": 0, "byok_usage_weekly": 0, "byok_usage_monthly": 0, "is_free_tier": false, "expires_at": null, "organization_id": null}
credits HTTP 200: {"total_credits": 10, "total_usage": 0.001}
key after the test calls: {"is_management_key": false, "is_provisioning_key": false, "limit": null, "limit_reset": null, "limit_remaining": null, "include_byok_in_limit": false, "effective_budget": null, "usage": 0.007748851, "usage_daily": 0.007748851, "usage_weekly": 0.007748851, "usage_monthly": 0.007748851, "byok_usage": 0, "byok_usage_daily": 0, "byok_usage_weekly": 0, "byok_usage_monthly": 0, "is_free_tier": false, "expires_at": null, "organization_id": null}

frontier intelligence index: 57.6 anthropic/claude-opus-5.5, 56 anthropic/claude-sonnet-5.5, 53.4 anthropic/claude-fable-5.1, 52.7 openai/gpt-6-astra, 52.6 google/gemini-4-argon, 51.8 openai/gpt-6.1-sol, 50.8 anthropic/claude-opus-5, 49.6 anthropic/claude-fable-5

| id | intelligence | in $/M | out $/M | image | ~$/call |
|---|---|---|---|---|---|
| xiaomi/mimo-v2.6-pro | 46.3 | 0.435 | 0.87 | True | 0.01175 |
| z-ai/glm-5.3 | 44.8 | 0.079 | 1.4 | False | 0.00958 |
| anthropic/claude-haiku-5.5 | 43.4 | 0.1 | 0.5 | True | 0.0045 |
| minimax/minimax-m3.1-flash | 42.7 | 0.15 | 0.6 | True | 0.00585 |
| z-ai/glm-5.3-flash | 41.8 | 0.005 | 0.199 | True | 0.00127 |
| inclusionai/ling-3.1-flash | 41.1 | 0.075 | 0.225 | False | 0.00248 |
| deepseek/deepseek-v4.1-flash-1017 | 39.5 | 0.15 | 0.6 | True | 0.00585 |
| openai/gpt-6-luna | 38.1 | 0.1 | 0.5 | True | 0.0045 |
| xiaomi/mimo-v2.6-flash | 37.9 | 0.14 | 0.28 | True | 0.00378 |
| openai/gpt-5.6-luna | 37.3 | 0.2 | 1.2 | True | 0.0102 |
| deepseek/deepseek-v4-flash-vision-exp | 34.8 | 0.216 | 0.647 | True | 0.00712 |
| deepseek/deepseek-v4-flash-0731 | 34.3 | 0.047 | 0.141 | False | 0.00155 |
| qwen/qwen3.8-27b | 33.7 | 0.2 | 2.5 | True | 0.018 |
| minimax/minimax-m3 | 29.2 | 0.3 | 1.2 | True | 0.0117 |
| upstage/solar-pro4 | 28.2 | 0.15 | 0.6 | False | 0.00585 |
| qwen/qwen3.6-plus | 27 | 0.325 | 1.95 | True | 0.01657 |
| nvidia/nemotron-3.5-super-vl | 26.5 | 0.15 | 0.5 | True | 0.00525 |
| xiaomi/mimo-v2.5-pro | 26 | 0.304 | 0.609 | False | 0.00821 |
| thinkingmachines/inkling-small | 25.7 | 0.45 | 1.2 | True | 0.01395 |
| tencent/hy3-preview | 25.3 | 0.18 | 0.6 | False | 0.0063 |
| qwen/qwen3.7-plus | 25.2 | 0.32 | 1.28 | True | 0.01248 |
| deepseek/deepseek-v4.1-flash | 24.7 | 0.3 | 1.2 | True | 0.0117 |
| inclusionai/ling-3.0-flash-vl | 24.6 | 0.06 | 0.18 | True | 0.00198 |
| deepseek/deepseek-v4-flash | 24.4 | 0.091 | 0.182 | False | 0.00246 |
| upstage/solar-mini4 | 24.1 | 0.05 | 0.2 | False | 0.00195 |
| qwen/qwen3.5-27b | 22.9 | 0.27 | 2.16 | True | 0.01701 |
| minimax/minimax-m2.7 | 22.8 | 0.3 | 1.2 | False | 0.0117 |
| minimax/minimax-m2.5 | 22.8 | 0.27 | 0.95 | False | 0.00975 |
| google/gemini-3.5-flash-lite | 22.2 | 0.3 | 2.5 | True | 0.0195 |
| z-ai/glm-4.7 | 22.2 | 0.54 | 1.98 | False | 0.01998 |

| id | HTTP | s | in tok | out tok | reasoning | cost $ | answer |
|---|---|---|---|---|---|---|---|
| xiaomi/mimo-v2.6-pro | 200 | 20.7 | 3840 | 939 | 840 | 0.00248733 | ```json
{"direction": "SELL", "confidence": 65, "stop_loss": 1.16850, "take_profit": 1.16420, "reason": "Strong bearish momentum in last two bars (94-95) broke  |
| anthropic/claude-haiku-5.5 | 200 | 5.4 | 3016 | 657 | 509 | 0.0006301 | {"direction": "SELL", "confidence": 60, "stop_loss": 1.16820, "take_profit": 1.16380, "reason": "Price has broken down from the 1.17192 swing high with consecut |
| minimax/minimax-m3.1-flash | 200 | 4.5 | 2784 | 256 | 191 | 0.000544875 | {"direction":"SELL","confidence":68,"stop_loss":1.16940,"take_profit":1.16330,"reason":"The sharp bearish reversal and sustained selling below 1.1680 favor cont |
| z-ai/glm-5.3-flash | 200 | 1.3 | 2591 | 131 | 39 | 0.00039738125 | {"direction": "SELL", "confidence": 68, "stop_loss": 1.17100, "take_profit": 1.16450, "reason": "After peaking at 1.17192 the pair has printed a strong bearish  |
| deepseek/deepseek-v4.1-flash-1017 | 200 | 12.5 | 2615 | 1303 | 1225 | 0.0008607 | {"direction": "SELL", "confidence": 63, "stop_loss": 1.16845, "take_profit": 1.16450, "reason": "Momentum turned bearish after lower highs from 1.1719 and a bre |
| openai/gpt-6-luna | 200 | 4.7 | 2584 | 264 | 209 | 0.000454925 | {"direction":"SELL","confidence":68,"stop_loss":1.16950,"take_profit":1.16320,"reason":"Price has formed a sequence of lower highs and lower lows, with the late |
| qwen/qwen3.8-flash | 200 | 64.6 | 3895 | 3807 | 3730 | 0.00237354 | {"direction": "SELL", "confidence": 68, "stop_loss": 1.16850, "take_profit": 1.16300, "reason": "The breakdown below the recent 1.169-1.171 consolidation with l |

---
name: stock
track: bonus
kind: local_knowledge
inputs: [symbol]
outputs: [price, change]
side_effect: false
requires_confirmation: false
---

# Stock Tool

This tool fetches the current trading price and change percentage of a stock or cryptocurrency by ticker symbol.

## When to use
Use this tool when the user asks for the current price, stock market values, or trading price of a specific company stock (e.g. AAPL, MSFT, GOOG) or cryptocurrency (e.g. BTC, ETH).

## When NOT to use
Do NOT use this tool if the ticker symbol cannot be determined or if the user is asking for general stock market news instead of a specific ticker price.

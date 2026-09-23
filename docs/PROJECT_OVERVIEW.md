# Project overview

A plain-language introduction, for anyone arriving at this repository.

## What we are building

A system that studies market data, forms its own hypotheses about when a
trade has a real statistical edge, tests them honestly, and then decides,
one situation at a time, whether to **buy**, **sell** or **do nothing**.
It records why it decided, measures what happened, and uses the results to
propose better hypotheses, which are tested before they are used.

## What makes it different from a typical trading bot

- **No built-in strategy.** Most bots encode one idea ("buy when RSI is
  low") and hope. This system has no favourite idea. Every idea, old or
  new, has to earn its place on data.
- **Doing nothing is a real answer.** The system is expected to say
  NO_TRADE most of the time, and that is by design.
- **Honesty is built in.** Every experiment is registered before it runs,
  failed experiments are kept, and results are judged against how many
  things were tried.
- **Its freedom is fenced.** The AI can choose what to trade and how, but a
  separate risk engine decides whether anything is actually sent to the
  broker, and at what size. The AI cannot get around it.

## Where it stands

**Phase 0: specification only.** There is no code. The documents in the
repository root are the contracts that the code must obey when it is
written.

## Why it starts this way

The predecessor project built a working bot first and asked afterwards
whether its strategy had an edge. After thorough, pre-registered testing
of thirteen strategy families, the answer was no, for all of them, even
before costs ([HISTORICAL_ARCHIVE.md](HISTORICAL_ARCHIVE.md)). This project
reverses the order: the rules for deciding whether something works are
fixed first, so that nothing can be built on an untested assumption.

## Honest expectations

Finding a durable edge in liquid markets is hard, and most attempts fail.
The most likely outcomes of this project, in order, are:

1. a well-built system that correctly concludes there is no edge in the
   data it has, and declines to trade;
2. a small edge in specific conditions, which the system trades rarely;
3. a larger edge.

All three are reported the same way: with the evidence, and nothing more.

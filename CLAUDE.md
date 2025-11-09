# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a trading bot repository for both crypto and stocks.

The project will be a monorepo containing python backend (the bot and other backend essentials) and a vuejs frontend in the same repository, so the root filesystem will be :

├── backend
├── frontend
├── CLAUDE.md

No other root file or folder must be created until the user allow it.

The project is a very evolutive project starting with creating a PoC then make it evolving to a full integrated auto trading system, so it must be develop with modularity and scalability in mind.

## Target structure

### Backend

The backend will basically contain :

- Data Features : data collect and cleaning
- Predictive features :
  - Pattern recognition (pennants, flags, wedges, triangles, ...);
  - Asset correlation;
  - Tehnical analysis (MACD, RSI, ...);
  - Sentiment analysis (Twitter, Reddit, ...);
  - Predictive ML : gradient boosting;
- Backtesting features : ability to test models on historicals data;
- Decision features : open position, hold, close;
- Exposed API for all the features.

### Frontend

The frontend will allow the user to follow its portfolio, its performance and to take action : open a position, or close on taken or not by the bot.

## PoC

The first goal of the PoC is to take decisions on the precise stack, tools, services to use and to make a proof of concept. Choices must be guided by :

1. Performance : the bot must be able to execute a decision few times after getting the signals to not lose;
2. Cost : as we'll execute a lot of order, cost is very important to not absorb all benefits;
3. Easiness of implementation and maintenance : the project will evolve a lot so modularity and saclability is key.

## Important Notes

- Ensure all trading logic is thoroughly tested before deployment
- Write clean and performant code, aligned with best proven code patterns
- Write short code module instead of multipurpose large code files
- Handle API rate limits and connection failures gracefully
- Implement proper logging for all trading decisions and transactions
- Never commit API keys or sensitive credentials

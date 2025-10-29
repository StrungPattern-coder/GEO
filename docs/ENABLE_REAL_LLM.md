# 🚀 Enable Real LLM for GEO

## Problem
The mock LLM returns generic templates instead of real answers.

## Solution: Use Ollama (Free Local LLM)

### Step 1: Install Ollama
```bash
# macOS
brew install ollama

# Or download from: https://ollama.com/download
```

### Step 2: Start Ollama and Pull a Model
```bash
# Start Ollama service
ollama serve

# In another terminal, pull a fast model
ollama pull llama3.2:3b
# OR for better quality:
# ollama pull llama3:8b
```

### Step 3: Update GEO Config
Create or edit `.env` file:
```bash
# Use Ollama for real answers
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b

# Keep web search enabled
SEARCH_PROVIDER=duckduckgo
```

### Step 4: Restart Backend
```bash
./RESTART_BACKEND.sh
```

### Step 5: Test!
Ask: "What is 2+2?"
Expected: "The answer is 4, which is the result of adding 2 and 2 together [1][2]."

---

## Alternative: Use OpenAI (Paid, Best Quality)

### Step 1: Get API Key
Get your API key from: https://platform.openai.com/api-keys

### Step 2: Update `.env`
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Restart
```bash
./RESTART_BACKEND.sh
```

---

## Alternative: Use Anthropic Claude (Paid)

### Step 1: Get API Key
Get your API key from: https://console.anthropic.com/

### Step 2: Update `.env`
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## Quick Comparison

| Provider | Cost | Quality | Speed | Setup |
|----------|------|---------|-------|-------|
| **Mock** | Free | ❌ Bad | ⚡ Instant | ✅ None |
| **Ollama** | Free | ✅ Good | 🟡 Medium | 🟡 5 min |
| **OpenAI** | $$ | ⭐ Best | ⚡ Fast | ✅ 1 min |
| **Anthropic** | $$ | ⭐ Best | ⚡ Fast | ✅ 1 min |

---

## 🎯 Recommendation

**Use Ollama** - it's free, runs locally, and gives you real intelligent answers!

```bash
# Quick setup (3 commands):
brew install ollama
ollama pull llama3.2:3b
echo 'LLM_PROVIDER=ollama\nOLLAMA_MODEL=llama3.2:3b' >> .env
```

Then restart the backend and you'll get actual intelligent answers! 🧠

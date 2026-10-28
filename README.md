# Orbit Log

A small script that builds a daily page with new papers and news about space robotics and AI.

It pulls recent papers from arXiv and stories from a few public RSS feeds, ranks them by keywords, and writes a two-sentence summary for each one with a "why it matters" line and a difficulty tag. Everything runs without an API key. If you want better summaries you can plug in an LLM (see below).

## Run it

```bash
python3 digest.py --out ./digest
```

By default it shows 2 papers and 3 news stories a day. Change that with `--papers` and `--news`.

Then open `digest/index.html`. Each day gets its own page and the script remembers what it already showed, so you never see the same item twice.

It only uses the Python standard library (3.9 or newer).

## Run it every evening

On Linux or macOS add a cron line, for example:

```
0 20 * * * cd /path/to/orbit-digest && python3 digest.py --out /path/to/digest
```

On Windows use Task Scheduler and point it at the same command.

## Better summaries with an LLM

Set these and the script will ask any OpenAI-compatible API (Groq, Ollama...) for the summaries. If a call fails it falls back to the built-in rules.

```bash
export LLM_BASE_URL=https://api.groq.com/openai/v1
export LLM_API_KEY=your-key
export LLM_MODEL=llama-3.1-8b-instant
```

## Tests

```bash
pip install pytest
pytest
```

## Notes

- Summaries are machine-made and can be wrong, so always open the link for the full text.
- The difficulty tag is a rough guess based on the vocabulary of the abstract.
- arXiv asks for at most one request every few seconds. The script makes a single request per run.

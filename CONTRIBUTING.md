# Contributing to Hermes Warmstart

## Setup

```bash
git clone https://github.com/diandian1001/hermes-warmstart.git
cd hermes-warmstart
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

Tests require Python 3.9+. 25 tests cover all core paths including:
- Scale structure validation
- Profile generation from all 243 answer combos
- Natural language description accuracy
- Agent instruction generation
- System prompt block integrity

## Project Structure

```
warmstart/
├── __init__.py      # Public API
├── profile.py       # Profile engine (PersonalityProfile)
├── scales.py        # Scale definitions (Big Five + extensible interface)
└── prompt.py        # Interactive CLI
```

## Adding a New Scale

Implement the `Scale` protocol:

```python
from warmstart import Scale

class MBTIScale(Scale):
    @property
    def questions(self) -> list[dict]:
        return [...]

    def parse_answers(self, answers: list[int]) -> dict:
        # Validate input, return dimension→score mapping
        ...
```

Then use it:

```python
from warmstart import PersonalityProfile
profile = PersonalityProfile.from_answers(answers, scale=MBTIScale())
```

## PR Guidelines

- Add tests for new functionality
- Run `python -m pytest tests/ -v` before pushing
- Keep the README in sync with code changes
- MIT licensed — all contributions welcome!

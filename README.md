# ragbase — Project Setup Guide

Anyone cloning this project follows these steps:

```bash
# 1. clone
git clone <your-repo-url>
cd ragbase

# 2. create virtual environment
python -m venv myenv

# 3. activate virtual environment
source myenv/bin/activate        # mac/linux
myenv\Scripts\activate           # windows

# 4. install everything (prod + dev dependencies)
pip install -e ".[dev]"

# 5. verify install worked
python -c "from ragbase import parser; print('ragbase ready')"
```

One virtual environment. One install command. Done.

---

twill: a simple scripting language for web browsing
===================================================

twill is a simple scripting language intended for programmatic or automated browsing of websites.

The current version 3.4 supports Python 3.10 to 3.15.

Take a look at the [changelog](https://twill-tools.github.io/twill/changelog.html) to find a list of all changes and improvements made since version 2. For a brief overview of twill's history starting from its early days, see the [acknowledgements and history](https://twill-tools.github.io/twill/overview.html#acknowledgements-and-history) section.

The full [documentation](https://twill-tools.github.io/twill/) is included in the distribution and provided online via [GitHub](https://twill-tools.github.io/twill/) and [ReadTheDocs](https://twill.readthedocs.io/en/latest/).

Using twill with AI coding agents
---------------------------------

The documentation is also provided in a form suitable for LLMs and coding agents as [llms.txt](https://twill-tools.github.io/twill/llms.txt) and [llms-full.txt](https://twill-tools.github.io/twill/llms-full.txt).

The repository contains an [agent skill](skills/twill/SKILL.md) that teaches coding agents how to write, run and debug twill scripts. In Claude Code, you can install it as a plugin with:

```
/plugin marketplace add twill-tools/twill
/plugin install twill@twill-tools
```

For other coding agents, copy the directory `skills/twill` into their skills directory, or use a skill installer that supports GitHub repositories.

Copyright (c) 2005-2026 by C. Titus Brown, Ben R. Taylor, Christoph Zwerschke et al.

Newer versions have been created and are maintained by [Christoph Zwerschke](https://github.com/Cito).
 
twill is available for use, modification, and distribution under the MIT license.

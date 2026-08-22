# Project Overview

The qqOne tool allows to maintain a knowledge-base and to query it using a generative AI.

# Architecture


```mermaid
---
title: qqOne Architecture
---
graph TD
    subgraph Q[qqOne]
        A
        B
    end
    U[User] -->|use| A
    U[User] -->|use| E
    A[qqOne CLI] -->|call| B["Dynamic Context"]
    B -->|read| C["Knowledge Base"]
    B -->|create| D["Context File"]
    E[Generative AI Prompt] -->|read| D
```

**qqOne**: Provides a command line prompt to interact with the qqOne suite.
**Dynamic Context**: Creates a context file to be sent to the generative AI.
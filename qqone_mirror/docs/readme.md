# qqOne

**qqOne** is a human-curated, AI-augmented knowledge base system designed to support daily engineering work of an individual developer or a small team. 

**qqOne** is multi-faceted:
- It defines the structure of the knowledge base.
- It defines the process for maintaining the knowledge base. 
- It provides a set of tools to create and maintain the knowledge base, and to use it as context for LLMs.


It's hard to name specific use-cases, as qqOne is more about a different way of working than a tool for doing something specific. Here are some examples:
- Handing over of knowledge about a project, a topic, or a task.
    The expert accumulate the information in the knowledge base, the successor can retrieve information from the knowledge base according to his/her speed, approach, cognitive style.
- Supporting explorative tasks around a new topic. 
    The knowledge base is used to accumulate the knowledge about the new topic. 
- Synergy between individual learning and incremental knowledge accumulation.
    As the user explores a topic and queries the LLM, the knowledge base grows richer with new information, insights, and ideas. This creates a virtuous cycle: learning drives enrichment, and enrichment drives deeper learning.
- Supporting day-by-day work, like reviews, design, brainstorming, etc.

What qqOne is not:

- qqOne **is not a RAG tool.** Specifically, it does not apply any offline indexing of the knowledge base nor any other kind of pipeline.

- qqOne **is not an LLM-wiki**, because such paradigm is intended to cover a very narrow topic.

    Example: an LLM-wiki can be used by a student to prepare an exam on a specific topic, but it is not suitable to cover the wide variety of a whole project.

- qqOne **is not a company-wide knowledge management system.** A single instance can cover the needs of an individual developer or a small team.
This is because the knowledge base must have a well focused scope, as it should be the focus of an individual developer or a small team.

    Example: Team1 works on version 1.0 of a software, while Team2 works on version 2.0. If they share the same instance of qqOne, it may be difficult for the tool to discriminate between the two versions.

## Background

In order to allow an LLM to provide answers related to your private context without retraining the model, you need to provide it with a additional information (context injection). This can be done by extending the prompt with your own data. 

The common solution for this is the RAG technique (Retrieval-Augmented Generation) that allows to process very large amounts of data, so that it can scale to the enterprise level. On the other side, it requires a complex toolchain to manage the multiple layers it needs (data-injestion, chunking, indexing, vector data-base creation, retrieval).

The qqOne's approach is different because it assumes that the user explicitly maintain the input data (knowledge base) by keeping the clean and focused.
This brings several advantages:
- The knowledge base is queried at real-time. This means that any information is available as soon as it is added to the knowledge base.
- The knowledge base is much more dense of information because it is manually curated. This means that the LLM can provide more accurate and relevant answers.
- For the same reasone we have a lower risk of retrieving obsolete information.
- There's also less risk of retrieving mismatching information. For example, the same components may have variants, but this is not visible by just downloading the Confluence pages.

## The Concept in a Nutshell

The qqFour's paradigm relies on the **knowledge base**, the **iterative workflow**, the **metadata**, and the **tools**.

**The knowledge base** is a collection of documents in markdown format. 

- The `imports` directory contains the files imported from multiple sources. Each file is tagged so that it can be easily retrieved, but apart from this the directory is unstructured. It's the main source of information.

- The `log.md` file is a chronological list of individual notes. It is essential to guarantee the richness of the knowledge base. 

<!-- TODO: log.md is owned by an individual person. This means that, when used, the output should go to an activity that is owned by an individual person -->

- The `activities` directory contains a number of independent activities, identified by the name of the directory. Each activity addresses a specific topic, project, or task. For example, an activity can be a design review, a brainstorming session, an exploration of a new topic, etc. 

**The iterative workflow**. The user is responsible for ensuring the quality of the knowledge base.
When working on an activity, the user shall execute iteratively the following operations:

- Ask questions to the LLM by using the context provided by the activity.
- Review and improve the existing `.md` files or create new ones.
- Include more information from the `imports` in the activity.
- Add new documents to the `imports` directory.

**The metadata** are used to establish links between documents. They are essential to allow the search tool to retrieve more accurate and relevant data.

**The tools** allow to import documents to the knowledge base, to search for existing 'activities', and to interact with the LLM.

## Principles and Benefits

**The consistency and focus**.
By relying on a manually curated knowledge base and on continuous improvement, qqFour ensures that the information is consistent and focused on the relevant topics. The common solution of using an automatic crawling may retrieve contradictory or obsolete information.

**The customized mental model**. 
In the traditional information flow, the author of the documents chooses how to organise the information, how ideas connect, and the order in which everything should be read. Furthermore, the author may omit implicit assumptions, contextual knowledge, and unstated relationships. 
On the other side, the readers may need to approach the content following different mental paths, or different combinations of ideas. 
As a result, the superficial structure of the documents becomes an obstacle. This is why readers are rarely fully satisfied with documentation, no matter how well it’s written. 
With qqFour, the readers compose the information in the way that matches their own reasoning. 

**The information density**. 
The log and the manually created document must contain pros and cons, hypotheses, assumptions, considerations, doubts, and counter-arguments.
This makes the information semantically rich, integrated and connected, regardless of the superficial structure of the documents. 
This allows the LLM to provide accurate and relevant answers.

**The scalable structure**. 
The scalable structure of the `imports` and  `activities` directories allows to manage dynamic and evolving contexts. It also allows a distributed management among the team members.

 **Digital Gardening**. Analogia col giardino: potatura, togliere erbacce, aggiungere nuove piante, ecc. Il giardino è sempre in evoluzione, e sempre curato. Non è mai finito. 

**Frictionless Capture**. Lo scopo è minimizzare il carico cognitivo tra il momento in cui si ha un'idea o si conosce una niuova informazione e il momento in cui la scrivi. The user can easily add new information to the knowledge base without worrying about the structure or organization. This encourages continuous updates and enrichment of the knowledge base.

## The Knowledge Base

A knowledge base is a collection of documents focused on a specific topic, characterised by a minimal structure, meaning that all files may be stored within a single directory.

It is a living resource that relies on users to correct errors, update existing content, add new information, and remove obsolete material.

qqOne accepts only Markdown files, as it's the most natural input and output for LLMs.

Usually, a development team uses one single knowledge base.

Diagrams are embedded directly in the Markdown documents and use human‑readable languages such as Mermaid or PlantUML. This allows a smoother workflow between the author and the generative AI. For example, the LLM can easily modify the diagrams or create new ones.

Some definitions:

- **1bf** : A **1bf** is an file generated by **qqOne** for its own processing. 
The name stands for **One Big File**, which reflects its purpose: it combines large amounts of extracted content into a single textual file.
It contains fragmented, unstructured information, it is not intended to be read or edited by the user.
It uses the extension `.1bf.txt`.

- **activity** : Activities are composed by a mix of generated `1bf` files, user-defined through a configuration file, and a set of manually maintained markdown documents.
Activities are typically used to track day-to-day work, ongoing tasks, ideas, or creative exploration.

- **log** : A manually maintained file that contains continuous updates on all subjects related to the knowledge base.
The incremental content is added from the top, so that the most updated items are on top.

## Most importand qqOne commands

- `topic` : Searches for a **topic’s 1bf** file and sends the full content to the AI chat.

- `aidynamic` : Given a search text, it browses the entire knowledge base, creates a **1bf**, and sends its content to the AI chat.



## Other components

### dynamic_context.py

Given a knowledge base and a question, this script creates the context file.

### keywords.py

The script extracts the most common words and ngrams from a knowledge base.

### qqone_bot.py

Telegram bot that provides access to LLMs online services.

### docx_to_txt.py

Utility to convert docx files to plain text files. Used to import Google Note files.  

### get_patterns.py

Calculate search patterns from a question. 


## More details

* qqOne is not integrated with the LLM. qqOne does not use the LLM’s API but instead produces a text file 
that is then used as context in GitHub Copilot chat.
*   qqOne only accepts text files as input. Importing from other formats (Polarion, PDFs, images, Confluence pages, Jira issues) 
must be done manually, even if supported by tools. In some sense, the retrieval part is missing.
*   The user must use only official TTTech’s AI providers, currently Copilot and GitHub Copilot license. Using other providers is strictly prohibited.
*   Ability to switch between different models offered by TTTech’s GitHub Copilot license. The results can vary significantly.
*   The model does not run locally.
*   Minimal development cost, and I have personally been using it for months (mid-2025) and find it very useful.
*   The knowledge base is handpicked and manually controlled. Only high-quality, relevant content is included. No automatic crawling.
*   The knowledge base is selected with strong criteria. Files are selected manually. Automatic crawling is not used.
*   I can create highly specific contexts (for example, a specific review activity or a Jira feature) and switch between contexts instantly. Perhaps this is possible with standard tools, but I haven’t managed to do it.
*   Extreme fine-tuning of context. For example, not just “Review Process in Polarion,” but “How the current Review Process in Polarion works?” and “How to improve the Review Process in Polarion.”
*   The database is not created automatically on a periodic basis. qqOne allows continuous refinement of the database (adding, removing, modifying files continuously). On one hand, this requires a slight overhead for each activity; on the other hand, the database is always up to date on current topics (zero delay).

*   Note that LLM works best with information-dense documents. Important decision are always enriched with rationales, assumtions, considerations. Add also consideration about pros and cons of every decision. 



## File extensions

The following files considered by qqOne as part of the knowledge-base:
- Files with extension .txt (textual plain text) or .md (Markdown).
- Files with extension *.1bf.txt (One Big File) are aggregated chunks and are not intended to be human readable.

The following files are ignored by qqOne when searching in the knowledge-base:
- Files named readme.txt or readme.md
- Files with extension *.gitignore.txt or *.gitignore.md (they are also ignored by git)

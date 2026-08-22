# qqFour

**qqFour** is a human-curated, AI-augmented knowledge base system designed to support information handling, thinking, exploration, and daily engineering work of an individual developer or a small team. 

It's hard to name specific use-cases, as qqFour is more about a different way of working than a tool for doing something specific. Here are some examples:
- Handing over of knowledge about a project, a topic, or a task.
    The expert accumulate the information in the knowledge base, the successor can retrieve information from the knowledge base according to his/her speed, approach, cognitive style.
- Supporting explorative tasks around a new topic. 
    The knowledge base is used to accumulate the knowledge about the new topic. 
- Synergy between individual learning and incremental knowledge accumulation.
    As the user explores a topic and queries the LLM, the knowledge base grows richer with new information, insights, and ideas. This creates a virtuous cycle: learning drives enrichment, and enrichment drives deeper learning.
- Supporting day-by-day work, like reviews, design, brainstorming, etc.

What qqFour is not:

- qqFour **is not a RAG tool.** Specifically, it does not apply any offline indexing of the knowledge base nor any other kind of pipeline.

- qqFour **is not an LLM-wiki**, because such paradigm is intended to cover a very narrow topic.

    Example: an LLM-wiki can be used by a student to prepare an exam on a specific topic, but it is not suitable to cover the wide variety of a whole project.

- qqFour **is not a company-wide knowledge management system.** A single instance can cover the needs of an individual developer or a small team.
This is because the knowledge base must have a well focused scope, as it should be the focus of an individual developer or a small team.

    Example: Team1 works on version 1.0 of a software, while Team2 works on version 2.0. If they share the same instance of qqFour, it may be difficult for the tool to discriminate between the two versions.

## The Concept in a Nutshell

The qqFour's paradigm relies on the **knowledge base**, the **iterative workflow**, the **metadata**, and the **tools**.

**The knowledge base** is a collection of documents in markdown format. 

- The `imports` directory contains the files imported from multiple sources. Each file is tagged so that it can be easily retrieved, but apart from this the directory is unstructured. It's the main source of information.

- The `log.md` file is a chronological list of individual notes. It is essential to guarantee the richness of the knowledge base. 

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

**Asynchronous knowledge transfer**.
Knowledge transfer can happen asynchronously through the knowledge base, reducing the need for frequent meetings and workshops. Newcomers can explore the topic at their own pace and deepen their understanding independently.

**Digital Gardening**. Analogia col giardino: potatura, togliere erbacce, aggiungere nuove piante, ecc. Il giardino è sempre in evoluzione, e sempre curato. Non è mai finito. 

**Frictionless Capture**. Lo scopo è minimizzare il carico cognitivo tra il momento in cui si ha un'idea o si conosce una niuova informazione e il momento in cui la scrivi. The user can easily add new information to the knowledge base without worrying about the structure or organization. This encourages continuous updates and enrichment of the knowledge base.

## The Knowledge Base

The knowledge base is a collection of documents. Usually, a development team uses one single knowledge base.
It is a living resource that requires the user to correct mistakes, add new information, and remove obsolete content.
It is composed of three key parts: the `imports` directory, the `log.md`, the `activities`. 

The `imports` directory contains the imported files, in markdown format, from multiple sources. Example sources can be email chats, meeting transcripts, Jira tickets, Confluence pages, PDF documents, etc. The user must ensure that only relevant and high-quality content is included. Automatic crawling cannot be used. This is essential to keep the knowledge base consistent and focused.

The knowledge base is composed only by plain text file or by Markdown files. Diagrams are embedded directly in the Markdown documents and use human‑readable languages such as Mermaid or PlantUML. This allows a smoother workflow between the author and the generative AI. For example, the LLM can easily modify the diagrams. 

The qqFour's paradigm assumes that the user explicitly maintains the knowledge base by keeping the clean and focused. Automatic crawling is not used.

This brings several advantages:
- The knowledge base must be kept small, so that it can be searched in real-time. This means that any information is available as soon as it is added to the knowledge base. Furthermore, this minimizes the usage of tokens.
- The knowledge base is much more dense of information because it is manually curated. This means that the LLM can provide more accurate and relevant answers.
- For the same reason it has lower risk of retrieving obsolete or inconsistent information.

Inside the knowledge base, you find the following directory structure:

```
kbx/
├── log.md
├── activities/
└── imports/
```

The `log.md` is a manually maintained file that contains continuous updates on all subjects related to the knowledge base. The incremental content is added from the top.
The `log.md` is continuously updated by the user by adding new information, insights, ideas, etc. The content is added from the top. Each new note must be self-contained and well contextualized. They are usually short, ranging from a single line to a few dozen. Notes often present pros and cons, hypotheses, assumptions, considerations, doubts, and counter-arguments, which makes them semantically very “dense”. The overall content of the file is fragmented and unstructured, but nevertheless, very dense.

Each Activity is typically used to track day-to-day work, ongoing tasks, ideas, or creative exploration. The `activities` directory has the following structure:

```
<name_of_the_activity>/
├── description.md                  # Description of the activity
├── <name>.md                       # Manually crafted documents. This is the 'output' of the activity
├── raw/
│   └── <name>.gitignore.1bf.txt    # Generated supporting files
├── 1bf_configs/
│   └── 1bf_config_<name>.yaml      # Configuration for the generation of the supporting files
└── scripts/
    └── <script_name>.py            # Activity specific scripts
```

An 'activity' contains the following type of files:

- `description.md` : It describes the purpose of the activity. It will be used by qqFour to help searching for the activities. This file is mandatory and it's created and maintained by the user.

- `<name>.md` : This is the 'output' of the activity. It's crafted by the user. There can be many of these files.

- `<name>.gitignore.1bf.txt`: A **1bf** ("One Big Files") is an internal file generated by **qqFour** by using data from the `imports` directory. It contains fragmented, unstructured information, and it is not intended to be read or edited by the user.

- `1bf_config_<name>.yaml` : each one of these files configures the generation of a `1bf` file. For example, it specifies which files must be collected from the imports directory. This files are created by the user.

- `<script_name>.py` : Optional activity-specific scripts that elaborates the imported data. For example, it can be used to compose the material for the reviews.

## The Workflow
    
The user continuously updates `log.md` with new information, insights, ideas, etc. The content is fragmented and unstructured. The essential point is that every note must be well contestualized by using proper wording. 

The user shall handpick and manually control the content of the knowledge base. Only high-quality, relevant content is included. No automatic crawling.

Note that LLM works best with information-dense documents. For this reason manually added information is always enriched with rationales, assumptions, considerations. Add also consideration about pros and cons of every decision.



As a general rule, the `.md` files should never explode in number and size, because the user should always keep the informative content of the activity under control. The rule of thumb is that qqFour knows a more than the user, but not too much more.


## The tool

**qqFour** is a command line shell.

- It allows to import documents from different sources, like Jira, Confluence, PDF documents, etc.
- It allows to search for existing 'activities'.
- Specific functionalities prepares the context for LLM's chat by using the 'imports' or the 'activity' directory. The script make use of fragmenting techniques, deduplication, and it preserves the metadata. The search is dynamic as it is based on the content of the knowledge base at the moment of the search. No offline pipelines are used.
- Generates the '1bf' files by using the information from the 'imports' directory.

## The Keywords

The links between concepts are established by using keywords. This is different from the typical approach of using backlinks.

The keywords are metadata manually added to the files.


The relationship that can be defined may have different semantics.

For example, the `Related` relationship is weaker than the `Keywords` one. The `Related` relationship is used to link documents that are loosely connected or alternative topics. The `Keywords` relationship is used to link documents that are closely related and share the same main subjects.

The `Context` relationship defines the specific domain or environment to which the document applies, helping to narrow search relevance. 

The `Alternatives` relationship lists concepts that are alternative to the one described in the document.

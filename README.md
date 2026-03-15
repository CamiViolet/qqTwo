<!--  Cmd + K V for the preview -->

# qqTwo

The qqTwo leverages the capabilities of LLMs in order to improve some common activities like code creation, document creation and review, and answering questions related to the knowledge base.

It's characterized by requiring human intervention in the creation and maintenance of the knowledge base. This is a key point because it allows to keep the knowledge base clean and focused on the relevant topics, which is crucial for the quality of the answers provided by the LLM.

## Dynamic Context

In order to allow the LLM to provide answers related to your private context without retraining the model, you need to provide it with a additional information (context injection). This is technically done by extending the prompt with your own data. 

The common solution for this is the RAG technique (Retrieval-Augmented Generation) that allows to process very large amounts of data, so that it can scale to the enterprise level. On the other side, it requires a complex toolchain to manage the multiple layers it needs (data-injestion, chunking, indexing, vector data-base creation, retrieval).

The qqTwo's approach is different because it assumes that the user explicitly maintain the input data (knowledge base) by keeping the clean and focused.
This brings several advantages:
- The knowledge base is queried at real-time. This means that any information is available as soon as it is added to the knowledge base.
- The knowledge base is much more dense of information because it is manually curated. This means that the LLM can provide more accurate and relevant answers.
- For the same reasone we have a lower risk of retrieving obsolete information.
- There's also less risk of retrieving mismatching information. For example, the same components may have variants, but this is not visible by just downloading the Confluence pages.

# Knowledge Base 'kb0'

The knowledge base is a collection of documents that are used by the tool qqTwo to create context files for the LLM.

The knowledge bases are named by using the convention kb<N> where <N> is a number that identify the specific knowledge base. 

The knowledge base kb0 is characterized by handling the following topics:
- MotionWise Classic: product from TTTech.
- MotionWise Communication: product from TTTech.

The knowledge base is composed only by plain text file or by Markdown files.

Diagrams are embedded directly in the Markdown documents and use human‑readable languages such as Mermaid or PlantUML. This provides allows a smoother workflow between the author and the generative AI. For example, the LLM can easily modify the diagrams. 


## Other components

### dynamic_context.py

Given a knowledge base and a question, theis script creates the context file.

### keywords.py

The script extracts the most common words and ngrams from a knowledge base.

### qqTwo_bot.py

Telegram bot that provides access to LLMs online services.

### docx_to_txt.py

Utility to convert docx files to plain text files. Used to import Google Note files.  

### get_patterns.py

Calculate search patterns from a question. 





## More details

* qqTwo is not integrated with the LLM. qqTwo does not use the LLM’s API but instead produces a text file 
that is then used as context in GitHub Copilot chat.
*   qqTwo only accepts text files as input. Importing from other formats (Polarion, PDFs, images, Confluence pages, Jira issues) 
must be done manually, even if supported by tools. In some sense, the retrieval part is missing.
*   The user must use only official TTTech’s AI providers, currently Copilot and GitHub Copilot license. Using other providers is strictly prohibited.
*   Ability to switch between different models offered by TTTech’s GitHub Copilot license. The results can vary significantly.
*   The model does not run locally.
*   Minimal development cost, and I have personally been using it for months (mid-2025) and find it very useful.
*   The knowledge base is handpicked and manually controlled. Only high-quality, relevant content is included. No automatic crawling.
*   The knowledge base is selected with strong criteria. Files are selected manually. Automatic crawling is not used.
*   I can create highly specific contexts (for example, a specific review activity or a Jira feature) and switch between contexts instantly. Perhaps this is possible with standard tools, but I haven’t managed to do it.
*   Extreme fine-tuning of context. For example, not just “Review Process in Polarion,” but “How the current Review Process in Polarion works?” and “How to improve the Review Process in Polarion.”
*   The database is not created automatically on a periodic basis. qqTwo allows continuous refinement of the database (adding, removing, modifying files continuously). On one hand, this requires a slight overhead for each activity; on the other hand, the database is always up to date on current topics (zero delay).

*   Note that LLM works best with information-dense documents. Important decision are always enriched with rationales, assumtions, considerations. Add also consideration about pros and cons of every decision. 


I want to build a similar system  (but at a much smaller scale for a beginner’s pace). This is a personal project for me to learn basics as a beginner by seeing and performing how this application was built, understand why each of the components were used and why the components and tech stack was selected.  You will make it very simple for me to understand and help construct a simple build to start.    

The tools i will have at my disposal currently are Cursor (preferred), ChatGPT/OpenAI API, Claude Desktop/Claude Code, Pinecone Vector DB.

The preferred stack:
	•	Frontend (Next.js + Tailwind): simple UI to upload files and show a structured summary/progress.  ￼
	•	Backend (FastAPI): receives the files, orchestrates the AI flow, streams progress back.  ￼
	•	AI core (LangChain/LangGraph, OpenAI GPT-4o): a small team of agents—Triage → Historical Analyst → Root-Cause Analyzer → Synthesizer—coordinate to read the uploads, pull context, and produce a final write-up.  ￼
	•	Retrieval (Pinecone + small embeddings): past postmortems are pre-ingested into a vector store; the agent retrieves relevant snippets to ground its answer. Use basic retrieval tricks native to Pinecone

Help me build and construct the technical stack needed for this project (least resistant path is best).  identify the pre-requisites needed before we begin building.  If there is a way to vibe code this rather than build from scratch like a traditional experienced full stack AI developer, please consider as option.    Always remember, from this point on, we need each step to have explicit step-by-step instruction with built-in verifications of step outputs to ensure there is functional accuracy before you provide next step action required from developer (me).   If i stumble and run into issues with each step, I will always provide you continuous input where current steps is and you will ask me (developer) whether each step in  progress and results are accurate before continue on to next step or until current step is remediated.    Do not forget this approach and remember to catch yourself if you begin to jump ahead of me with assumptions of my understanding.  Avoid repeating steps of verification if you've already provided them earlier to me  unless i explicitly ask again.    For now, review our requirments and provide your understanding first what our objective here is.


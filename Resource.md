Tools and Technologies
CockroachDB
AWS
About the Sponsors
FAQ
 
CockroachDB
CockroachDB Cloud — Start Free — Spin up a free cluster in minutes. No credit card required.
Managed MCP Server Quickstart — Log into Cloud Console → select your cluster → copy the MCP config snippet → paste into Claude Code, Cursor, or VS Code.
ccloud CLI Documentation — Install, authenticate with a service account, and start driving infrastructure from your terminal.
CockroachDB Agent Skills Repo (GitHub) — Open-source, machine-executable skills for onboarding, operations, performance, security, and observability.
pgvector + CockroachDB (Distributed Vector Search) — Integrated vector indexing for semantic search and RAG at scale.
LangChain × CockroachDB — Provider, Vector Store, and Chat Message History integrations.
 
AWS
AWS Free Tier — Hands-on experience with AWS services at no cost.
 

About the Sponsors
CockroachDB
CockroachDB is a globally distributed operational database platform built to support the full lifecycle of AI-driven applications, from early prototypes to production systems and autonomous agents. It is no longer just an architectural preference, it is a necessity.

CockroachDB serves as the system of record for agentic memory, giving AI agents a single, resilient place to persist state, context, embeddings, and structured data. Built on an always-on architecture trusted by companies like OpenAI (ChatGPT), UiPath, CoreWeave, and Automation Anywhere, it unifies transactional and semantic workloads in one system. Fully PostgreSQL-compatible, with elastic serverless scaling and enterprise-grade security at every layer, CockroachDB enables AI agents to evolve from deterministic SQL-based tasks to semantic reasoning and long-running workflows without sacrificing context, consistency, or control.

Amazon Web Services (AWS)
AWS is the world's most comprehensive and broadly adopted cloud platform, offering over 200 fully featured services from data centers globally. With Amazon Bedrock, AWS makes it easy for developers to build and scale generative AI applications using foundation models from Anthropic, Meta, Amazon, and more with the security, compliance, and scalability that enterprises require.

 

Support
Join the Cockroach Labs Slack


 
FAQ
Do I need to pay to use CockroachDB?
No. CockroachDB Cloud has a free tier that is fully eligible for this hackathon. You can spin up a cluster in minutes at cockroachlabs.cloud with no credit card required.

Can I use other AI models besides Claude?
Yes. The CockroachDB MCP Server supports any MCP-compatible client, and the Agent Skills Repo is model-agnostic, it works with Claude, Cursor, LangChain, or your own agent framework. You must use at least one AWS service, but you can use any combination of models.

What if I'm new to CockroachDB?
Perfect. The hackathon starter kits are designed to get you from zero to a running agent in under 30 minutes. CockroachDB is fully PostgreSQL-compatible, so if you know Postgres, you already know most of CockroachDB.

Can I use CockroachDB for the vector/embedding store and the transactional store?
Yes, and this is one of CockroachDB's key differentiators for agentic workloads. CockroachDB's integrated pgvector support with distributed indexing means you can store embeddings and transactional data in one system, eliminating ETL complexity and consistency issues between a separate vector store and your operational database.

What is the Model Context Protocol (MCP)?
MCP is an open standard created by Anthropic that allows AI agents to safely and predictably interact with external systems: tools, databases, APIs, through a structured, auditable interface. CockroachDB's Managed MCP Server implements this protocol to give AI coding agents like Claude Code and Cursor a direct, secure connection to your database cluster.

What are Agent Skills?
Agent Skills are structured, machine-executable capabilities published in CockroachDB's open-source skills repository. Each skill encodes a specific CockroachDB workflow like 'profile statement fingerprints' or 'detect schema anti-patterns'  with clear inputs, outputs, and behavior. Skills follow open, standard interfaces so they work across models and agent frameworks without rewriting integrations. Think of them as reusable building blocks for production-grade database operations.
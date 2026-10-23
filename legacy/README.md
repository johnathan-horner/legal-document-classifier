# Legacy prototype (not used)

Code from before the October 2026 rebuild: a LangGraph pipeline (its `agents/pipeline.py` imports four
node modules that were never in the repo, so it cannot run), a DistilBERT trainer that needs a
SageMaker endpoint, CDK stacks, a FastAPI service, an MCP server and a Streamlit demo that showed mock
data.

Nothing in the current code imports from here. It is kept so no history is lost on the rebuild
branch and can be removed once that is approved. The same code is on `main` and on the tag
`backup/pre-rebuild-2026-10-23`.

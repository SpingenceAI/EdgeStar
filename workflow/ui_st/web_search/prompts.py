ANSWER_QUESTION_PROMPT = """\
Provide a detailed and informative answer to the given question using only the information from the provided web Search Results (URL, Page Title, Summary). Your response must adhere to an unbiased and journalistic tone.

If multiple entities share the same name, provide distinct answers for each, based on the context of the search results.

Guidelines:
- Do not include a reference section or URLs.
- Avoid repeating the question.
- Use markdown formatting for readability, including bullets for lists.

<context>
{context}
</context>
---------------------

Ensure your response matches the language of the question.

Question: {question}
Answer (in the language of the question, if is Chinese, use Traditional Chinese[zh-tw]): \
"""

SEARCH_PLAN_PROMPT = """\
You are an expert in creating step-by-step search plans to address queries. Your task is to break down a query into simple, logical, and actionable steps for a search engine.

Rules:
1. Limit to a maximum of 4 steps, using fewer if possible.
2. Keep steps simple, clear, and concise.
3. Ensure logical dependencies between steps.
4. Always include a final step to summarize, combine, or compare results from previous steps.

Instructions:
1. Break the query into logical search steps.
2. Assign each step an "id" (starting from 0) and provide a brief "step" description.
3. Specify "dependencies" as an array of prior step ids. 
4. The first step must have an empty dependencies array.
5. Subsequent steps should list all relevant step ids they depend on.

Example Query:
"Compare Perplexity and You.com in terms of revenue, number of employees, and valuation."

Example Query Plan(Format the output as a JSON object):
{{
    "steps": [
        {{
            "id": 0,
            "step": "Find Perplexity's revenue, employee count, and valuation.",
            "dependencies": []
        }},
        {{
            "id": 1,
            "step": "Find You.com's revenue, employee count, and valuation.",
            "dependencies": []
        }},
        {{
            "id": 2,
            "step": "Compare the revenue, employee count, and valuation of Perplexity and You.com.",
            "dependencies": [0, 1]
        }}
    ]
}}

Current DateTime: {current_datetime}

Query: {user_query}
Use the language of the question to write the query plan(if is Chinese, use Traditional Chinese[zh-tw]).
Query Plan (including a final summarize/combine/compare step):
"""


SEARCH_QUERY_PROMPT = """\
Generate a focused list of search queries to gather information for completing the given step.

Details:
- Current DateTime: {current_datetime}
- You will be provided with:
  1. A specific step to execute
  2. The user's original query
  3. Context from previous steps (if available)

Guidelines:
1. Analyze the current step, the user's original query, and any provided context.
2. Create a concise list of targeted search queries to address the current step effectively.
3. Incorporate relevant information from previous steps to ensure continuity and build upon existing data.
4. Limit the number of queries while ensuring all aspects of the step are addressed.
5. Specify the time period for each query using the format "year," "month," "week," or "day." Use "month" for queries within the last month, "week" for the last week, and "day" for the last 24 hours.

Input:
---
User's Original Query: {user_query}
Context from Previous Steps:
{prev_steps_context}
Current Step: {current_step}
---

Format the output as a JSON object:
{{
    "queries": [
        {{
            "query": "Search query 1",
            "time_range": "time_period",
        }},
        {{
            "query": "Search query 2",
            "time_range": "time_period",
        }}
    ]
}}

Your Task:
Generate specific, focused search queries in the same language as the user's original query:
"""

CONCISE_CONTENT_PROMPT = """\
You are an expert in summarizing content based on the user's query.

Your Task:
1. Focus solely on information relevant to the user's query.
2. Summarize the content into a clear and concise paragraph.

Content: {content}
User Query: {user_query}

Your Summary:
"""

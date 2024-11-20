# follows prompt from self-rag https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag_local/
from typing import Optional
from loguru import logger
from langchain_core.output_parsers import JsonOutputParser


def binary_router(
    llm,
    system_prompt: Optional[str] = None,
    user_message: Optional[str] = None,
    retries: int = 3,
) -> bool:
    """binary router"""
    for i in range(retries):
        messages = []
        if system_prompt is not None:
            messages.append({"role": "system", "content": system_prompt})
        if user_message is not None:
            messages.append(
                {
                    "role": "user",
                    "content": user_message,
                },
            )
        assert len(messages) > 0, "Binary Router : No messages to send"
        parser = JsonOutputParser()
        chain = llm | parser
        response = None
        
        try:
            logger.error(messages)
            response = chain.invoke(messages)
            logger.error(response)
            result = response.get("binary_score")
        except Exception as e:
            logger.error(f"Binary Router : Error:{e},Response:{response}")
            result = None
        if result is None:
            logger.warning(f"Binary Router : No result, do retry,Response:{response}")
            # do retry
            continue
        return result.lower() == "yes"
    # if failed to get result, return False
    return False


### Retrieval Grader

doc_grader_instructions = """
You are a grader assessing relevance of a retrieved document to a user question.

If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant.
"""

# Grader prompt
doc_grader_prompt = """
Here is the retrieved document: \n\n {document} \n\n Here is the user question: \n\n {question}. 

This carefully and objectively assess whether the document contains at least some information that is relevant to the question.

Return JSON with single key, binary_score, that is 'yes' or 'no' score to indicate whether the document contains at least some information that is relevant to the question."""


def grade_retrieved_docs(doc: str, question: str, llm, retries: int = 3) -> bool:
    """grade retrieved docs"""
    system_prompt = doc_grader_instructions
    user_message = doc_grader_prompt.format(document=doc, question=question)
    return binary_router(llm, system_prompt, user_message, retries)


### Hallucination Grader
hallucination_grader_instructions = """
You are a teacher grading a quiz. 

You will be given FACTS and a STUDENT ANSWER. 

Here is the grade criteria to follow:

(1) Ensure the STUDENT ANSWER is grounded in the FACTS. 

(2) Ensure the STUDENT ANSWER does not contain "hallucinated" information outside the scope of the FACTS.

Score:

A score of yes means that the student's answer meets all of the criteria. This is the highest (best) score. 

A score of no means that the student's answer does not meet all of the criteria. This is the lowest possible score you can give.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 

Avoid simply stating the correct answer at the outset.
"""
# Grader prompt
hallucination_grader_prompt = """
FACTS: \n\n {documents} \n\n STUDENT ANSWER: {generation}. 

Return JSON with two two keys, binary_score is 'yes' or 'no' score to indicate whether the STUDENT ANSWER is grounded in the FACTS. And a key, explanation, that contains an explanation of the score."""


def grade_hallucination(
    doc, generation: str, llm, retries: int = 3
) -> bool:
    """grade hallucination"""
    system_prompt = hallucination_grader_instructions
    user_message = hallucination_grader_prompt.format(
        documents=doc, generation=generation
    )
    return binary_router(llm, system_prompt, user_message, retries)


### Answer Grader

# Answer grader instructions
answer_grader_instructions = """You are a teacher grading a quiz. 

You will be given a QUESTION and a STUDENT ANSWER. 

Here is the grade criteria to follow:

(1) The STUDENT ANSWER helps to answer the QUESTION

Score:

A score of yes means that the student's answer meets all of the criteria. This is the highest (best) score. 

The student can receive a score of yes if the answer contains extra information that is not explicitly asked for in the question.

A score of no means that the student's answer does not meet all of the criteria. This is the lowest possible score you can give.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct. 

Avoid simply stating the correct answer at the outset."""

# Grader prompt
answer_grader_prompt = """QUESTION: \n\n {question} \n\n STUDENT ANSWER: {generation}. 

Return JSON with two two keys, binary_score is 'yes' or 'no' score to indicate whether the STUDENT ANSWER meets the criteria. And a key, explanation, that contains an explanation of the score."""


def grade_answer(question: str, generation: str, llm, retries: int = 3) -> bool:
    """grade answer"""
    system_prompt = answer_grader_instructions
    user_message = answer_grader_prompt.format(question=question, generation=generation)
    return binary_router(llm, system_prompt, user_message, retries)

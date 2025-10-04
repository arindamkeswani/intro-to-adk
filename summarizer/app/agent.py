from google.adk.agents import Agent 

def compute_word_reduction(original_text: str, summarized_text: str) -> dict:
    """
    Computes word count stats and percentage reduction between
    the original and summarized text.

    Args:
        original_text (str): The full original input text.
        summarized_text (str): The summarized version of the text.

    Returns:
        dict: A dictionary containing original word count, new word count,
              and percentage reduction.
    """
    original_count = len(original_text.split())
    new_count = len(summarized_text.split())

    if original_count == 0:
        reduction = 0
    else:
        reduction = ((original_count - new_count) / original_count) * 100

    return {
        "original_word_count": original_count,
        "new_word_count": new_count,
        "percentage_reduction": round(reduction, 2)
    }


# Summarizer Agent
root_agent = Agent(
    name="summarizer",
    model="gemini-2.0-flash",
    description="Agent that summarizes input text and computes word reduction statistics.",
    instruction=(
        "You are a concise summarization assistant. "
        "Your goal is to summarize the provided input text in **less than 30 words**. "
        "Do not add any commentary. "
        "**CRITICAL STEP:** After generating the summary, you must call the "
        "`compute_word_reduction` tool, providing your generated summary text as arguments. "
        "Finally, combine your summary and the results of the tool into one "
        "human-friendly, easy-to-read response."
    ),
    # Only include the necessary tool for computation.
    tools=[compute_word_reduction] 
)

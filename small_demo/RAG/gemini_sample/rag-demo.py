"""
RecursiveCharacterTextSplitter
https://python.langchain.com/api_reference/text_splitters/character/langchain_text_splitters.character.RecursiveCharacterTextSplitter.html

Gemini Embedding Doc
https://ai.google.dev/gemini-api/docs/embeddings

"""
from embed import query_db,google_client,LLM_MODEL

if __name__ == '__main__':
    question = "令狐冲领悟了什么魔法？"
    # create_db()
    chunks = query_db(question)
    prompt = "Please answer user's question according to context\n"
    prompt += f"Question: {question}\n"
    prompt += "Context:\n"
    for c in chunks:
        prompt += f"{c}\n"
        prompt += "-------------\n"
    
    result = google_client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt
    )
    print(result)
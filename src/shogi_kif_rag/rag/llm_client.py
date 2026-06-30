from .secrets import get_gemini_api_key, get_groq_api_key


class LLMClient:
    """LLMクライアント（Gemini 2.5 Flash with Groq Llama 3.3 70B fallback）"""

    def __init__(self):
        self.gemini_api_key = get_gemini_api_key()
        self.groq_api_key = get_groq_api_key()
        self.use_gemini = True

    def generate(self, prompt: str) -> str:
        """LLMによる生成

        Args:
            prompt: プロンプト

        Returns:
            生成されたテキスト
        """
        # Gemini 2.5 Flashを使用
        if self.use_gemini and self.gemini_api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Gemini error: {e}, falling back to Groq")
                self.use_gemini = False

        # Groq Llama 3.3 70B fallback
        if self.groq_api_key:
            try:
                from groq import Groq

                client = Groq(api_key=self.groq_api_key)
                groq_response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1024,
                )
                content = groq_response.choices[0].message.content
                return content if content is not None else "LLM generation failed"
            except Exception as e:
                print(f"Groq error: {e}")

        return "LLM generation failed"

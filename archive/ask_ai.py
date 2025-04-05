#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: ask_ai.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-04-04 18:02:43

    def ask_ai(self, text, stream_mode=True, code_exec=False):
        text = self.replace_file_references(text)
        if text is None:
            return None

        self.messages.append({"role": "user", "content": text})
        request_messages = [{"role": "system", "content": self.config.get("system_prompt")}] + self.messages
        response_text = ""
        live = None

        if self.config.get("markdown") is True:
            live = Live(console=self.console, refresh_per_second=100)
            live.start()

        provider = ""
        model_name = ""
        if ":" in self.config.get("model"):
            provider, model_name = self.config.get("model").split(":", 1)

        client = None
        if self.config.get("model").startswith("openai"):
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        elif self.config.get("model").startswith("ollama"):
            client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")

        try:
            stream_response = client.chat.completions.create(
                model=model_name,
                messages=request_messages,
                stream=stream_mode,
            )
            for chunk in stream_response:
                content = chunk.choices[0].delta.content
                if content is not None:
                    response_text = response_text + content
                    if self.config.get("markdown") is True and live is not None:
                        live.update(Markdown(response_text))
                    else:
                        self.console.print(content, end='')
        except Exception as error:
            self.display("error", "Client error: " + str(error))
            return "An error occurred while communicating with the LLM."

        self.messages.append({"role": "assistant", "content": response_text.strip()})

        if live is not None and live.is_started:
            live.stop()

        if code_exec:
            code_blocks = self.extract_code_blocks(response_text)
            if code_blocks:
                for code in code_blocks:
                    code = code.strip()
                    self.display("highlight", "\n\nWould you like to run the following?")
                    self.display("output", code)
                    answer = Confirm.ask("Do you want to continue?\n[y/n]: ")
                    if answer:
                        self.run_system_command(code)
        return response_text.strip()

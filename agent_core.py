"""
Agent Core - Núcleo del Agente Inteligente para LPMS
Versión 4.0 - Integración con LangChain y Gemini 2.5-pro
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory

# --- Importar TODAS las herramientas ---
from agent_tools import (
    generar_escrito_mediacion_tool,
    calculadora_matematica_tool,
    solicitar_nueva_herramienta_tool,
    generar_acuerdo_ia_tool,
    generar_acuerdo_template_tool,
    generar_acuerdo_integrado_tool,
    leer_plantilla_tool
)

# --- Carga de Prompts Externos ---
try:
    with open("persona.txt", "r", encoding="utf-8") as f:
        PERSONA_PROMPT = f.read()
    with open("react_instructions.txt", "r", encoding="utf-8") as f:
        OPERATIONAL_PROMPT = f.read()
except FileNotFoundError as e:
    print(f"ERROR: No se encontró un archivo de prompt requerido: {e.filename}")
    exit()

# --- Plantilla de Ensamblaje para Gemini ---
REACT_PROMPT_TEMPLATE = """
{persona_prompt}
{operational_prompt}

You are an AI assistant specialized in mediation agreement generation. You have access to various tools to help you create professional legal documents.

TOOLS AVAILABLE:
{tools}

INSTRUCTIONS:
- Always think step by step about what you need to do
- Use the available tools when necessary to gather information or perform actions
- For agreement generation, first read the template file, then use the case data to create the document
- Be thorough and professional in your responses
- When generating agreements, ensure all case details are properly incorporated

RESPONSE FORMAT:
Question: the input question you must answer
Thought: your reasoning about what to do next
Action: the tool to use (if needed), must be one of [{tool_names}]
Action Input: the input parameters for the tool
Observation: the result from the tool
... (repeat Thought/Action/Action Input/Observation as needed)
Final Answer: your complete response to the user

Begin your work:

Question: {input}
Thought: {agent_scratchpad}
"""

class AgentCore:
    def __init__(self):
        print("Inicializando el Núcleo del Agente v4.0 (Gemini 2.5-pro)...")

        # Cargar variables de entorno
        load_dotenv()

        # Configurar Gemini
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en el archivo .env")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",  # Usando gemini-2.5-pro como especificado por el usuario
            google_api_key=gemini_api_key,
            temperature=0.1,
            max_tokens=4096,
            verbose=True
        )

        # --- Lista completa de herramientas ---
        self.tools = [
            generar_escrito_mediacion_tool,
            calculadora_matematica_tool,
            solicitar_nueva_herramienta_tool,
            generar_acuerdo_ia_tool,
            generar_acuerdo_template_tool,
            generar_acuerdo_integrado_tool,
            leer_plantilla_tool
        ]
        print(f"Herramientas cargadas: {[tool.name for tool in self.tools]}")

        self.prompt = PromptTemplate.from_template(REACT_PROMPT_TEMPLATE).partial(
            persona_prompt=PERSONA_PROMPT,
            operational_prompt=OPERATIONAL_PROMPT,
            tools="\n".join([f"{tool.name}: {tool.description}" for tool in self.tools]),
            tool_names=", ".join([tool.name for tool in self.tools]),
        )
        print("Prompts ensamblados.")

        # Crear el Agente ReAct
        react_agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        print("Agente ReAct creado.")

        # Inicializar la Memoria de la conversación
        self.memory = ConversationBufferWindowMemory(
            k=5,
            return_messages=True,
            memory_key="chat_history",
            output_key="output"
        )
        print("Memoria de conversación (últimas 5 interacciones) inicializada.")

        # Crear el Ejecutor del Agente (el motor que une todo)
        self.agent_executor = AgentExecutor(
            agent=react_agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
        )
        print("="*30)
        print("Núcleo del Agente (Gemini 2.5-pro) listo para operar.")
        print("="*30)

    def run_intent(self, user_intent: str):
        """
        Ejecuta una intención del usuario a través del agente usando Gemini.
        """
        try:
            print(f"\n---> [USUARIO] PROCESANDO INTENCIÓN: '{user_intent}'")

            # Usar invoke con el formato correcto para Gemini
            response = self.agent_executor.invoke({
                "input": user_intent,
                "chat_history": []  # Inicializar historial de chat vacío
            })

            output = response.get("output", "No se obtuvo una respuesta clara.")
            print(f"[AGENTE] Respuesta generada exitosamente")
            return output

        except Exception as e:
            error_msg = f"Error procesando la intención con Gemini: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg


# ==============================================================================
# === BLOQUE DE PRUEBA PARA EJECUTAR DESDE LA CONSOLA =======================
# ==============================================================================

if __name__ == "__main__":
    # Instanciamos el cerebro de nuestro agente
    agent_core = AgentCore()

    print("\n--- INICIANDO PRUEBA AUTOMÁTICA DE HERRAMIENTA ---")
    print("Vamos a pedirle al agente que use la herramienta que creamos...")

    # Simular una petición completa con todos los datos para la herramienta
    test_intent = (
        "Hola, necesito tu ayuda. Por favor, genera un escrito de mediación para el caso con ID 99. "
        "El monto de la compensación acordado es de '250000'. "
        "El plazo para el pago es de '45' días. "
        "Los datos bancarios del actor para la transferencia son: Banco Santander, "
        "CBU '0720123456789012345678', alias 'maria.gomez.legal', y CUIT '27-98765432-1'."
    )

    # Ejecutar la prueba automática
    test_response = agent_core.run_intent(test_intent)
    print("\n\033[92m" + "--- RESPUESTA DE LA PRUEBA AUTOMÁTICA ---" + "\033[0m")
    print(test_response)
    print("----------------------------------------\n")

    # Iniciar bucle de conversación interactivo para que puedas chatear con él
    print("--- INICIANDO MODO DE CHAT INTERACTIVO ---")
    print("Puedes hablar con el agente. Escribe 'salir' para terminar.")

    while True:
        try:
            user_input = input("\033[94m" + "TÚ: " + "\033[0m")
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("Finalizando sesión...")
                break

            response = agent_core.run_intent(user_input)

            print("\n\033[92m" + "AGENTE:" + "\033[0m")
            print(response)
            print("-" * 20)
        except KeyboardInterrupt:
            print("\nFinalizando sesión por interrupción.")
            break
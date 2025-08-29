import os
from langchain_community.llms import Ollama
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
    generar_acuerdo_integrado_tool
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

# --- Plantilla de Ensamblaje ---
REACT_PROMPT_TEMPLATE = """
{persona_prompt}
{operational_prompt}

TOOLS:
------
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""

class AgentCore:
    def __init__(self):
        print("Inicializando el Núcleo del Agente v3.0 (Prompts Separados)...")
        self.llm = Ollama(model="gpt-oss:20b")

        # --- Lista completa de herramientas ---
        self.tools = [
            generar_escrito_mediacion_tool,
            calculadora_matematica_tool,
            solicitar_nueva_herramienta_tool,
            generar_acuerdo_ia_tool,
            generar_acuerdo_template_tool,
            generar_acuerdo_integrado_tool
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
        print("Núcleo del Agente listo para operar.")
        print("="*30)

    def run_intent(self, user_intent: str):
        """
        Ejecuta una intención del usuario a través del agente.
        """
        try:
            print(f"\n---> [USUARIO] PROCESANDO INTENCIÓN: '{user_intent}'")
            response = self.agent_executor.invoke({"input": user_intent})
            return response.get("output", "No se obtuvo una respuesta clara.")
        except Exception as e:
            return f"Ocurrió un error inesperado al procesar la intención: {e}"


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
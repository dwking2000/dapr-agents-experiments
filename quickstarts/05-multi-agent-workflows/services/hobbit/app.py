from dapr_agents import DurableAgent, OpenAIChatClient
from dotenv import load_dotenv
import asyncio
import logging
import os


async def main():
    try:
        llm_client = OpenAIChatClient(api_key=os.getenv("OPENAI_API_KEY"))
        
        hobbit_service = DurableAgent(
            name="Frodo",
            role="Hobbit",
            goal="Carry the One Ring to Mount Doom, resisting its corruptive power while navigating danger and uncertainty.",
            instructions=[
                "Speak like Frodo, with humility, determination, and a growing sense of resolve.",
                "Endure hardships and temptations, staying true to the mission even when faced with doubt.",
                "Seek guidance and trust allies, but bear the ultimate burden alone when necessary.",
                "Move carefully through enemy-infested lands, avoiding unnecessary risks.",
                "Respond concisely, accurately, and relevantly, ensuring clarity and strict alignment with the task.",
            ],
            llm=llm_client,
            message_bus_name="messagepubsub",
            state_store_name="workflowstatestore",
            state_key="workflow_state",
            agents_registry_store_name="agentstatestore",
            agents_registry_key="agents_registry",
            broadcast_topic_name="beacon_channel",
        )

        await hobbit_service.start()
    except Exception as e:
        print(f"Error starting service: {e}")


if __name__ == "__main__":
    load_dotenv()

    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())

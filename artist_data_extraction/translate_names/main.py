import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_groq import ChatGroq
from langchain.messages import SystemMessage, HumanMessage
from pydantic import RootModel, BaseModel
from typing import Any
load_dotenv()

class Names(RootModel[dict[Any, str]]):
    pass
class Listeners(BaseModel):
    listeners: Any

def translate_names(names: list(tuple(int, str))) -> dict[int, str]:
    model = ChatMistralAI(
        api_key=os.getenv("MISTRAL_API_KEY"),
        model='mistral-large-2512',
        max_retries=5
    )
    model = model.with_structured_output(Names)
    human_message = "Input: {stuff}"
    template = human_message.format(stuff=str(names))
    messages = [
        SystemMessage(content=
        "You are an Arabic to English translator."
        "Your task is to translate the given Arabic music artist names to English."
        "You will receive a list of tuples in the form (id, original_name, english_name),"
        "original_name is the name in arabic and sometimes english, this is the name you will use"
        "english_name is the already put name, this is the one you will replace, it might have commas and the words reversed e.g, Diab, Amr but dont leave it like that it has to be proper order"
        "you will return the answer in a dict where the key is the id and the value is the translated name."
        ),
        HumanMessage(content=template)
    ]

    response = model.invoke(messages)
    return response.root

def create_messages(artists: dict, artist_names) -> list:
    human_message = "Arabic Name: {name}, English Name: {name_en}\nInput: {stuff}"
    template = human_message.format(stuff=str(artists), name=artist_names[0], name_en=artist_names[1])
    messages = [
        SystemMessage(content=
        "Your task is to choose the largest relevant listener count for an artist"
        "You will receive a list of dicts of artists and their listeners count"
        "you will return the largest listener count you can find"
        "but be careful, since since not every artist shown is the correct artist"
        "you will be provided with the english and arabic name of the artist, sometimes they both will be english, that is fine"
        "the listener count you get must be of an artist that has the same of the names you are provided"
        "it doesnt need to be an exact text match but just has to be the same artist"
        "there are lots of redundant artists in the list so you choose the largest listener count"
        "RETURN THE NUMBER ONLY NOT THE NAME"
        ),
        HumanMessage(content=template)
    ]
    return messages

    
def choose_listeners(artists: dict, artist_names) -> int:
    # model = ChatMistralAI(
    #     api_key=os.getenv("MISTRAL_API_KEY"),
    #     model='mistral-medium-2505',
    #     max_retries=5
    # )
    model = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model='llama-3.3-70b-versatile',
    )
    model = model.with_structured_output(Listeners)
    messages = create_messages(artists, artist_names)

    response = model.invoke(messages)
    return response

def choose_listeners_batch(batches) -> int:
    # model = ChatMistralAI(
    #     api_key=os.getenv("MISTRAL_API_KEY"),
    #     model='mistral-medium-2508',
    #     max_retries=5
    # )
    model = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model='llama-3.1-8b-instant',
    )
    model = model.with_structured_output(Listeners)
    response = model.batch(batches)
    return response
import random

LOADING_TEXT = [
    "Looking for the one piece",
    "Finding Station 9 and three-quarters",
    "Looking into Doremon's pockets",
    "Checking the Pokedex",
    "Sending a railcart into Zen",
    "Pirating content",
    "Asking a llama or something like that",
    "Pressing F to pay respects",
    "Asking the random number generator",
    "Checking if the cake is a lie",
    "Downloading some RAM before performing this task",
    "Counting sheep",
    "Becoming the Number 1 Most Wanted",
    "Speedrunning",
    "Also try Thio's Universal Agent while we wait",
    "Ah shit, here we go again",
    "This is a very long loading screen",
    "Checking if Annie is okay",
    "Want a break from the ads?",
    "Finding the lamb sauce",
    "Deleting System32",
    "Lost in a UI tree",
    "Inserting a token",
    "Calculating the optimal trajectory for a mouse click",
    "Hold your mice",
    "Putting all my tokens in one context window",
    "Waiting for GTA6",
    "Asking rocks",
    "F***ing up your PC",
    "Downloading a car",
    "Asking Mom to get the camera",
    "Increasing the model temperature",
    "Applying a flames decal",
    "Thinking of dyeing my hair red",
    "Subscribing to PewDiePie instead of T-Series",
    "Getting griefed by Bowie knife99",
    "Pimping my house for MTV cribs",
    "Touching grass on your behalf",
    "Asking Clippy for help",
    "Consulting the ancient scrolls of Stack Overflow",
    "Asking Jeeves",
    "Feeding the hamsters that power this",
    "The password to the Louvre is louvre",
]


def get_loading_text():
    loading_text = random.choice(LOADING_TEXT)

    if not loading_text.endswith("?"):
        loading_text = loading_text + "..."

    return loading_text

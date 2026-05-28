import random

# {task} will be replaced with the event title
# {time} will be replaced with the event start time

REMINDER_MESSAGES = [
    "Hey girly! 💖\nTime to do the task: *{task}*\nYou got thissssssss!! 🌟",
    "Pssst! 🌸 Reminder alert!\n*{task}* is coming up at {time}!\nYou're literally gonna crush it 💪✨",
    "Hi bestie! 🎀\n*{task}* starts at {time}!\nYou're so capable and amazing, go get 'em!! 🦋",
    "⏰ Ding ding ding!\nTime for: *{task}* at {time}!\nBelieve in yourself, you're a STAR ⭐💫",
    "Gentle reminder from your biggest fan 🤍\n*{task}* is up at {time}!\nYou've totally prepared for this, go shine!! 🌙✨",
    "Heyyyy gorgeous! 🌺\n*{task}* is happening at {time}!\nYou're unstoppable and I believe in you SO much 💕",
    "🌈 Good news: it's time for *{task}*!\nStarting at {time} — and guess what?\nYou are MORE than ready 🌟🙌",
    "Rise and slay, bestie! 🔥\n*{task}* starts at {time}!\nRemember: you're that girl. Always. 💅✨",
    "💌 A little note from the universe:\nTime for *{task}* at {time}!\nYou are capable of INCREDIBLE things 🌙💫",
    "🎉 EVENT TIME!\n*{task}* starts at {time}!\nTake a deep breath... you've GOT this! 🫶",
]

STARTING_NOW_MESSAGES = [
    "IT'S HAPPENING!! 🚨💖\n*{task}* is starting RIGHT NOW!\nGo go go — you're amazing!! 🌟",
    "THIS IS YOUR MOMENT! ✨🎀\n*{task}* is starting NOW!\nYou were born for this!! 💪🌸",
    "NOW NOW NOW! 🔔💫\n*{task}* has started!\nYou've got all the power in the world, babe 🌺",
    "SHOWTIME!! 🎬✨\n*{task}* is live!\nGive it everything you've got — I believe in you 💕🌙",
    "💥 Go time, superstar!\n*{task}* starts NOW!\nYou are so ready for this, I'm cheering you on!! 🎉🙌",
]

MORNING_MESSAGES = [
    "Good morning, sunshine! ☀️\nYou have *{task}* today at {time}!\nToday is going to be amazing because YOU are amazing 💛🌸",
    "Rise & shine, bestie! 🌅\nDon't forget: *{task}* at {time} today!\nYou've got a wonderful day ahead 💫✨",
    "Morning reminder! ☕🌷\n*{task}* is on your schedule today at {time}!\nYou're going to do great, I just know it 💖",
]


def get_reminder_message(task: str, time_str: str) -> str:
    template = random.choice(REMINDER_MESSAGES)
    return template.format(task=task, time=time_str)


def get_starting_now_message(task: str) -> str:
    template = random.choice(STARTING_NOW_MESSAGES)
    return template.format(task=task, time="now")


def get_morning_message(task: str, time_str: str) -> str:
    template = random.choice(MORNING_MESSAGES)
    return template.format(task=task, time=time_str)

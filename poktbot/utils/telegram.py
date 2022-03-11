from telethon import Button


def build_layout(layout_definition):
    """
    Translates a layout definition to classes that can be sent through the TelegramBot.

    Example definition:
        layout_definition = [
            [
                {
                    "caption": "Button1",
                    "action": "action1"
                },
                {
                    "caption": "Button2",
                    "action": "action2"
                }
            ],
            {
                "caption": "Button3",
                "action": "action3"
            }
        ]

        Example result:
        ([
            [Button.inline("Button1"), Button.inline("Button2")],
            Button.inline("Button3")
        ],
        {
            "Button1": "action1",
            "Button2": "action2",
            "Button3": "action3",
        })

    :param layout_definition:
    :return:
    """
    actions = {}
    layouts = []

    for l in layout_definition:

        if type(l) is list:
            layout, more_actions = build_layout(l)
        else:
            layout = Button.inline(l['caption'])
            more_actions = {l['caption']: l['action']}

        layouts.append(layout)
        actions.update(more_actions)

    return layouts, actions

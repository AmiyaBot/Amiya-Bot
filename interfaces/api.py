from core.resource.arknightsGameData import ArknightsGameData


class Api:
    @classmethod
    async def _get_operator_by_name(cls, name: str):
        operators = ArknightsGameData().operators

        if name not in operators:
            return f'没有找到干员{name}'

        data = operators[name]
        stories = data.stories()

        for item in stories:
            if item['story_title'] == '客观履历':
                return item['story_text']

        return f'没找到干员{name}的客观履历'
